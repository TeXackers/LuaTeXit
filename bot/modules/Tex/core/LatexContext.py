import asyncio
import logging
import re
import shutil
import time
from contextlib import suppress
from typing import ClassVar

import discord
from anyio import Path as AsyncPath
from cmdClient import Context, cmdClient
from logger import log
from utils.ratelimit import Bucket, BucketFull, BucketOverFull

from modules.Tex.module import latex_module as module
from modules.Tex.resources import default_preamble, failed_image_path, staging_root

from .LatexGuild import LatexGuild
from .LatexUser import LatexUser
from .tex_utils import ParseMode, TexNameStyle


class LatexContext:
    __slots__ = (
        "_dm_source",
        "_errors",
        "_force_wide",
        "_header_collapsed",
        "_header_name",
        "_header_shown",
        "_last_reaction",
        "_lifetime_task",
        "_mask_id",
        "_output_message",
        "_show_emoji",
        "_source_deletion_task",
        "_source_message",
        "_source_shown",
        "_spoiler_output",
        "ctx",
        "keepsourcefor",
        "lguild",
        "luser",
        "preamble",
        "source",
        "wide",
    )

    # Compiled regex for the `$` latex content checker
    single_dollars_pattern = re.compile(r"\$(?=\S)[^$]+(?<=\S)\$")
    double_dollars_pattern = re.compile(r"\$\$[^$]+\$\$")

    # Cheap pre-filter for the autotex message parser
    autotex_trigger_pattern = re.compile(r"```|\$|\\\(|\\\[|\\begin\{")

    # Locks to avoid simultaneous compilation for each user
    user_locks: ClassVar[dict[int, asyncio.Lock]] = {}  # userid: Lock

    # Buckets to ratelimit latex requests
    user_buckets: ClassVar[dict[int, Bucket]] = {}  # userid: Bucket

    # Collection of LatexContexts listening for reactions by output message id
    active_contexts: ClassVar[dict[int, LatexContext]] = {}

    # Time to stay active for, after the last reaction
    active_lifetime = 300

    # Emojis, populated on initialisation
    emoji_delete: ClassVar[str | None] = None
    emoji_show_source: ClassVar[str | None] = None
    emoji_show_errors: ClassVar[str | None] = None
    emoji_delete_source: ClassVar[str | None] = None

    def __init__(self, ctx: Context, source, lguild=None, luser=None, wide=None, spoiler=False, **kwargs):
        self.ctx = ctx
        self.source = source
        self.lguild = lguild or LatexGuild.get(ctx.guild.id if ctx.guild else 0)
        self.luser = luser or LatexUser.get(ctx.author.id)
        self._mask_id: str | None = kwargs.get("mask_id")

        # One-time forced compile flags
        self._force_wide = wide

        # Cached configuration properties, loaded from user and guild
        self.wide = self.get_wide()
        self.keepsourcefor = self.get_keepsourcefor()
        self.preamble = self.get_preamble()

        # Pre-compile parameters
        self._source_message = ctx.msg
        self._dm_source = len(source) > 1000
        self._header_name = self.get_header_name()
        self._spoiler_output = spoiler

        # Running latex state
        self._errors: str | None = None
        self._output_message: discord.Message | None = None
        self._source_shown = False
        self._header_collapsed: str | None = None
        self._header_shown: str | None = None
        self._show_emoji: str | None = None
        self._source_deletion_task: asyncio.Task | None = None
        self._lifetime_task: asyncio.Task | None = None
        self._last_reaction: float | None = None

    # Compute configuration in current context from user, guild, and defaults
    def get_preamble(self):
        """
        Retrieve the current compilation preamble.
        """
        return self.luser.preamble or self.lguild.preamble or default_preamble

    def get_wide(self):
        return self._force_wide if self._force_wide is not None else self.luser.alwayswide

    def get_keepsourcefor(self):
        return self.luser.keepsourcefor

    def get_header_name(self):
        match self.luser.namestyle:
            case TexNameStyle.HIDDEN:
                name = ""
            case TexNameStyle.MENTION:
                name = f"<@{self.luser.id}>"
            case TexNameStyle.DISPLAYNAME:
                raw_name = self.ctx.author.display_name
                name = f"-# {discord.utils.escape_mentions(discord.utils.escape_markdown(raw_name))}"
            case TexNameStyle.USERNAME:
                raw_name = self.ctx.author.name
                name = f"-# {discord.utils.escape_mentions(discord.utils.escape_markdown(raw_name))}"
            case TexNameStyle.RUNNINGAS:
                target_name: str = self._mask_id
                sender_name: str = str(self.ctx.author.id)
                name = f"-# <@{discord.utils.escape_mentions(discord.utils.escape_markdown(sender_name))}> running as <@{discord.utils.escape_mentions(discord.utils.escape_markdown(target_name))}>"
            case _:
                raise ValueError(f"Unknown LatexUser namestyle `{self.luser.namestyle}`.")
        return name

    def get_header(self):
        return self._header_shown if self._source_shown else self._header_collapsed

    async def dm_source(self, target):
        embed = discord.Embed(
            title="LaTeX source",
            description=f"```latex\n{self.source}\n```",
            timestamp=self._source_message.created_at,
        )
        embed.set_footer(text="Sent at")
        embed.set_author(name=self._header_name)

        if self._errors:
            embed.add_field(
                name="Compile Errors",
                value="```{}```".format(self._errors.replace("```", "")),
                inline=False,
            )

        embed.add_field(
            name="Jump link",
            value=f"[Click here to jump back to the message]({self._output_message.jump_url})",
            inline=False,
        )
        try:
            await target.send(embed=embed)
        except discord.Forbidden:
            await self.ctx.error_reply(
                f"Could not direct message you {target.mention}, do you have me blocked or direct messages disabled?",
            )

    async def delete_source(self, delay=0):
        """
        Delete the source message, possibly after the configured delay.
        Don't run the deletion if the message was edited since we started.
        """
        try:
            if self._source_message:
                if delay:
                    # Wait for the delay, and abort if the message has been edited while we wait
                    last_modified = self._source_message.edited_at or self._source_message.created_at
                    await asyncio.sleep(delay)
                    if self._source_message.edited_at and last_modified < self._source_message.edited_at:
                        return
                await self._source_message.delete()
        except asyncio.CancelledError:
            pass
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass

    async def cleanup_staging(self, targetid: int) -> None:
        """
        Remove the target's staging directory in the background.

        Called once the compiled png has already been read and uploaded, so as to reclaim tmpfs
        """
        with suppress(asyncio.CancelledError):
            await asyncio.to_thread(shutil.rmtree, f"{staging_root}/{targetid}", ignore_errors=True)

    async def lifetime(self):
        """
        Asynchronously block until the context deactivates.
        """
        if self._lifetime_task:
            await self._lifetime_task

    # Maps each supported engine to the ctx.make* util that compiles it
    _engine_compilers: ClassVar[dict[str, str]] = {
        "tex": "makeluatex",
        "lua": "makeluatex",
        "luatex": "makeluatex",
        "lualatex": "makeluatex",
        "pdftex": "maketex",
        "pdflatex": "maketex",
        "pdf": "maketex",
        "xetex": "makexetex",
        "xelatex": "makexetex",
        "plain_luatex": "make_plain_luatex",
        "plainlua": "make_plain_luatex",
        "plain_pdftex": "make_plain_pdftex",
        "plainpdf": "make_plain_pdftex",
        "pythontex": "makepythontex",
        "pytex": "makepythontex",
    }

    async def _compile(self, engine: str):
        """
        Compile the source using the ctx.make* util registered for `engine`.
        """
        make_fn = getattr(self.ctx, self._engine_compilers[engine])
        return await make_fn(self.source, self.luser.id, self.preamble, self.luser.colour, pad=not self.wide)

    async def _make(self, engine: str) -> discord.Message | None:
        """
        Make the latex message, handling ratelimits, compilation using the given engine, and output.
        """
        ctx = self.ctx
        luser = self.luser

        # typing
        typing_indicator = asyncio.ensure_future(ctx.ch.typing())
        typing_indicator.add_done_callback(lambda fut: fut.exception())

        # Retrieve and request the user's bucket, creating if required
        if luser.id not in self.user_buckets:
            self.user_buckets[luser.id] = Bucket(5, 20)

        try:
            self.user_buckets[luser.id].request()
        except BucketOverFull:
            # A warning was already given, fail silently
            log("Aborting compile due to `BucketOverfull`.", context=f"{ctx.msg.id}", level=logging.INFO)
            return None
        except BucketFull:
            log("Aborting compile due to BucketFull`.", context=f"{ctx.msg.id}", level=logging.INFO)
            # Ratelimit warning
            await ctx.error_reply("Too many requests, please slow down!\n(You may try again in `5` seconds.)")
            return None

        # Retrieve the user lock, creating it if required
        if luser.id not in self.user_locks:
            self.user_locks[luser.id] = asyncio.Lock()

        async with self.user_locks[luser.id]:
            # Don't compile if the bucket is already overfull
            if self.user_buckets[luser.id].overfull:
                log("Aborting compile due to a newly overfull bucket.", context=f"{ctx.msg.id}", level=logging.INFO)
                return None

            # Compile the source
            error = await self._compile(engine)
            self._errors = error
            if error == "list":
                error = None
                self._errors = None

            # Build header messages, presented above LaTeX output image
            if self._dm_source:
                source_message = "```fix\nLaTeX source sent via direct message.\n```"
            else:
                source_message = "```latex\n{}\n```".format(self.source.replace("```", ""))

            if error:
                self._show_emoji = self.emoji_show_errors
                self._header_shown = "{}\n{}Compilation error:```{}```".format(
                    self._header_name,
                    source_message,
                    error.replace("```", ""),
                )
                self._header_collapsed = (
                    f"{self._header_name}\n## Compile Error!\n"
                    f"Click the {self._show_emoji} reaction to view the error message.\n"
                    "-# (You may also edit your message to recompile.)"
                )
            else:
                self._show_emoji = self.emoji_show_source
                self._header_shown = f"{self._header_name}\n{source_message}"
                self._header_collapsed = self._header_name

            # Fire deletion of source, if required
            if not error and self.keepsourcefor is not None:
                self._source_deletion_task = asyncio.ensure_future(self.delete_source(delay=self.keepsourcefor))
                self.ctx.tasks.append(self._source_deletion_task)

            # Obtain the output image path, potentially the failed image
            file_path_staged: AsyncPath = AsyncPath(f"{staging_root}/{luser.id}/{luser.id}.png")
            exists = await file_path_staged.is_file()
            file_path = AsyncPath(failed_image_path) if not exists else file_path_staged

            # Build the file object for sending, possibly spoilered
            output_file = discord.File(file_path, spoiler=exists and self._spoiler_output)

            # Finally, send the output and start the reaction handler
            try:
                self._output_message = await self.ctx.reply(
                    content=self._header_collapsed,
                    file=output_file,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                self._lifetime_task = asyncio.ensure_future(self.activate_reactions())
                self.ctx.tasks.append(self._lifetime_task)
            except discord.Forbidden:
                pass

            # purge storage if successful (no need for logs)
            if exists:
                cleanup_task = asyncio.ensure_future(self.cleanup_staging(luser.id))
                self.ctx.tasks.append(cleanup_task)

        return self._output_message

    async def make(self):
        """
        Make the latex message, handling ratelimits, compilation using PDFLaTeX, and output.
        """
        return await self._make("pdflatex")

    async def luatexmake(self):
        """
        Make the latex message, handling ratelimits, compilation using LuaLaTeX, and output.
        """
        return await self._make("luatex")

    async def xetexmake(self):
        """
        Make the latex message, handling ratelimits, compilation using XeLaTeX, and output.
        """
        return await self._make("xetex")

    async def plain_luatex_make(self):
        """
        Make the latex message, handling ratelimits, compilation using Plain LuaTeX, and output.
        """
        return await self._make("plain_luatex")

    async def plain_pdftex_make(self):
        """
        Make the latex message, handling ratelimits, compilation using Plain PDFTeX, and output.
        """
        return await self._make("plain_pdftex")

    async def pythontexmake(self):
        """
        Make the latex message, handling ratelimits, compilation using LuaLaTeX and PythonTEX, and output.
        """
        return await self._make("pythontex")

    async def activate_reactions(self):
        """
        Register this LatexContext as an active listener and add the reactions
        """
        ctx = self.ctx
        msg = self._output_message
        if msg is None:
            raise RuntimeError("activate_reactions() must run after the output message is sent")
        if self._show_emoji is None:
            raise RuntimeError("activate_reactions() must run after compilation has set the show emoji")
        if self.emoji_delete is None or self.emoji_delete_source is None:
            raise RuntimeError("emoji_delete/emoji_delete_source must be populated by LatexContext.init() before use")

        # Quit early if we can't add reactions, nothing to listen for
        if ctx.guild and not ctx.ch.permissions_for(ctx.guild.me).add_reactions:
            return

        try:
            # Register the context
            self._last_reaction = time.time()
            self.active_contexts[msg.id] = self

            # Add the emojis
            await msg.add_reaction(self.emoji_delete)
            await msg.add_reaction(self._show_emoji)
            if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                await msg.add_reaction(self.emoji_delete_source)

            # Keep waiting until we have been idle longer than our lifetime
            await asyncio.sleep(self.active_lifetime)

            # Clear the reactions we added
            if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                await msg.clear_reaction(self.emoji_delete)
                await msg.clear_reaction(self._show_emoji)
                if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                    await msg.clear_reaction(self.emoji_delete_source)
        except asyncio.CancelledError:
            log(
                "LatexContext lifetime cancelled, probably due to an edit.",
                context=f"mid:{self.ctx.msg.id}",
                level=logging.DEBUG,
            )
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass
        finally:
            # Unregister the context
            self.active_contexts.pop(msg.id, None)

    @staticmethod
    def extract_codeblocks(text):
        """
        Extract discord-style codeblocks from provided text.
        This ignores escaping.
        """
        blocks = []

        if "```" in text:
            splits = text.split("```")
            content_blocks = [splits[i] for i in range(1, len(splits), 2)]
            for content_block in content_blocks:
                splits = content_block.split("\n", maxsplit=1)
                if len(splits) == 2 and splits[0] and " " not in splits[0].strip():
                    blocks.append((splits[0].strip(), splits[1].strip()))
                else:
                    blocks.append((None, content_block.strip()))
        return blocks

    @classmethod
    def parse_content(cls, content: str, mode: ParseMode):
        """
        Build potential LaTeX from message content, depending on the parse mode.
        """
        # Extract codeblocks
        codeblocks = cls.extract_codeblocks(content)
        if codeblocks:
            # Build list of relevant blocks
            blocks = [block[1] for block in codeblocks if block[0] in ["", "tex", "latex"]]
        else:
            # Strip any wrapping backtics from content
            if content.startswith("`") and content.endswith("`"):
                content = content[1:-1]

            # No codeblocks, parse the original content
            blocks = [content]

        if blocks:
            # Parse depending on the parse mode
            match mode:
                case ParseMode.DOCUMENT:
                    source = "\n\n".join(blocks)
                case ParseMode.GATHER:
                    source = "\n".join([f"$\\begin{{gathered}}\n{block}\n\\end{{gathered}}$" for block in blocks])
                case ParseMode.ALIGN:
                    source = "\n".join([f"$\\begin{{aligned}}\n{block}\n\\end{{aligned}}$" for block in blocks])
                case ParseMode.TIKZ:
                    source = "\n".join([f"\\begin{{tikzpicture}}\n{block}\n\\end{{tikzpicture}}" for block in blocks])
                case _:
                    # This should be impossible
                    raise ValueError("Unknown `mode` passed to LaTeX parser.")
        else:
            # No content
            source = None

        return source

    @classmethod
    def weak_hastex(cls, content):
        r"""
        Weak Latex content checker.
        Checks whether there is a `$\S` followed by `\S$` anywhere in the content.
        (`\S` is a non-whitespace character).
        """
        if not content:
            return False

        if "$" in content and content.strip("$"):
            # Regex match for the $ pattern
            return cls.single_dollars_pattern.search(content) is not None
        return False

    @classmethod
    def strict_hastex(cls, content):
        r"""
        Strict Latex content checker.
        Checks for one of the following conditions:
            - At least two `$$` in the content.
            - A latex environment (by `\begin{` and `\end{`).
            - A latex mathmode macro (i.e. {`\(`, `\)`} and {`\[`, `\]`}).
        """
        if not content:
            return False

        has_tex = False

        # Check for `$$`
        # old code:
        # has_tex = has_tex or (content.count('$$') > 1
        #   and content.strip('$')
        #   and cls.double_dollars_pattern.search(content) is not None)
        has_tex = has_tex or (
            content.count("$$") > 1 and content.strip("$") and cls.double_dollars_pattern.search(content) is not None
        )

        # Check for environments
        has_tex = has_tex or ((r"\begin{" in content) and (r"\end{" in content))

        # Check for mathmode macros
        has_tex = has_tex or ((r"\(" in content) and (r"\)" in content))

        return has_tex or ((r"\[" in content) and (r"\]" in content))


async def reaction_listener(client: cmdClient, reaction, user):
    # Extractions for faster lookups
    lctx = LatexContext.active_contexts.get(reaction.message.id)

    # Ignore reaction if it isn't from an active context
    if lctx is None:
        return

    # Ignore reaction if it is from me
    if user == client.user:
        return

    luser = lctx.luser
    ctx = lctx.ctx

    # We can't guarantee the state stays consistent through multiple awaits
    # Multiple reactions may even be used simultaneously
    # So wrap this is a general try block to avoid spitting out unhandled exceptions
    with suppress(discord.NotFound, discord.Forbidden):
        if reaction.emoji == LatexContext.emoji_delete:
            # Check permissions
            if user.id == luser.id or (ctx.guild and ctx.ch.permissions_for(user).manage_messages):
                # Cancel all tasks (in particular cancelling the activate_reactions sleep and unregistering it)
                [task.cancel() for task in ctx.tasks]

                # Delete the output message
                await reaction.message.delete()
        elif reaction.emoji in [LatexContext.emoji_show_source, LatexContext.emoji_show_errors]:
            # Check the user is the author or if they allow other people to view the source
            if user.id == luser.id or reaction.message.channel.permissions_for(user).manage_messages:
                # Toggle the shown state
                lctx._source_shown = not lctx._source_shown

                # Update the message
                await reaction.message.edit(content=lctx.get_header())

                # DM if required
                if lctx._source_shown and lctx._dm_source:
                    await lctx.dm_source(user)

                # Attempt to remove the user's reaction
                if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                    await reaction.remove(user)
        elif reaction.emoji == LatexContext.emoji_delete_source and (
            user.id == luser.id or (ctx.guild and ctx.ch.permissions_for(user).manage_messages)
        ):
            # Cancel any running source deletion task
            if lctx._source_deletion_task:
                lctx._source_deletion_task.cancel()

            # Request immediate source deletion
            await lctx.delete_source()

            # Attempt to clear the reaction
            # If the reaction appears at all, we probably have manage_messages
            if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                await reaction.clear()


@module.init_task
def attach_emojis(client: cmdClient):
    LatexContext.emoji_delete = client.conf.emojis.getemoji("delete")
    LatexContext.emoji_show_source = client.conf.emojis.getemoji("latex_show_source")
    LatexContext.emoji_show_errors = client.conf.emojis.getemoji("latex_show_errors")
    LatexContext.emoji_delete_source = client.conf.emojis.getemoji("latex_delete_source")


@module.init_task
def register_reaction_listener(client: cmdClient):
    client.add_after_event("reaction_add", reaction_listener)


@module.init_task
def attach_latex_locks(client: cmdClient):
    # Attach user simultaneous rendering locks
    client.objects["latex_user_locks"] = LatexContext.user_locks

    # Attach user leaky buckets
    client.objects["latex_user_buckets"] = LatexContext.user_buckets
