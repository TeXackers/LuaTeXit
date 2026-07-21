import asyncio
import logging
import shutil
from contextlib import suppress
from typing import ClassVar

import discord
from anyio import Path as AsyncPath
from cmdClient import Context, cmdClient  # noqa
from logger import log
from utils.ratelimit import Bucket, BucketFull, BucketOverFull

from modules.Tex.core.LatexContext import LatexContext
from modules.Tex.core.tex_utils import TexNameStyle
from modules.Typst.resources import default_preamble, failed_image_path, staging_root

from .TypstLayouts import TypstOutputView
from .TypstUser import TypstUser


class TypstContext:
    __slots__ = (
        "colour",
        "ctx",
        "header_name",
        "preamble",
        "source",
        "tuser",
    )

    # Locks to avoid simultaneous compilation for each user
    user_locks: ClassVar[dict[int, asyncio.Lock]] = {}

    # Buckets to ratelimit typst requests
    user_buckets: ClassVar[dict[int, Bucket]] = {}

    def __init__(self, ctx: Context, source: str, tuser: TypstUser | None = None):
        self.ctx = ctx
        self.source = source
        self.tuser = tuser or TypstUser.get(ctx.author.id)
        self.preamble = self.tuser.preamble or default_preamble
        self.colour = self.tuser.colour
        self.header_name = self.get_header_name()

    def get_header_name(self) -> str:
        """
        Build the header name shown above the output, per the (LaTeX-shared)
        `namestyle` setting.
        """
        match self.tuser.namestyle:
            case TexNameStyle.HIDDEN:
                return ""
            case TexNameStyle.MENTION:
                return f"<@{self.tuser.id}>"
            case TexNameStyle.USERNAME:
                raw_name = self.ctx.author.name
                return f"-# {discord.utils.escape_mentions(discord.utils.escape_markdown(raw_name))}"
            case _:
                # DISPLAYNAME/NICKNAME, and RUNNINGAS (which has no meaning here
                # since there's no Typst equivalent of the LaTeX `texas` "run as"
                # command) both fall back to the guild nickname/display name.
                raw_name = self.ctx.author.display_name
                return f"-# {discord.utils.escape_mentions(discord.utils.escape_markdown(raw_name))}"

    @classmethod
    def parse_content(cls, content: str) -> str | None:
        """
        Build potential Typst source from message content.
        Reuses `LatexContext.extract_codeblocks`, which is generic
        Discord-codeblock-splitting logic with no LaTeX-specific behaviour.
        """
        codeblocks = LatexContext.extract_codeblocks(content)
        if codeblocks:
            blocks = [block[1] for block in codeblocks if block[0] in ["", "typst", "typ"]]
        else:
            # Strip any wrapping backticks from content
            if content.startswith("`") and content.endswith("`"):
                content = content[1:-1]
            blocks = [content] if content else []

        if not blocks:
            return None

        return "\n\n".join(blocks)

    async def cleanup_staging(self, targetid: int) -> None:
        """
        Remove the target's staging directory in the background.
        Called once the compiled png has already been read and uploaded, so as to reclaim tmpfs.
        """
        with suppress(asyncio.CancelledError):
            await asyncio.to_thread(shutil.rmtree, f"{staging_root}/{targetid}", ignore_errors=True)

    async def make(self) -> discord.Message | None:
        """
        Compile the source, handling ratelimits, and send the compiled output.
        """
        ctx = self.ctx
        tuser = self.tuser

        # typing
        typing_indicator = asyncio.ensure_future(ctx.ch.typing())
        typing_indicator.add_done_callback(lambda fut: fut.exception())

        # Retrieve and request the user's bucket, creating if required
        if tuser.id not in self.user_buckets:
            self.user_buckets[tuser.id] = Bucket(5, 20)

        try:
            self.user_buckets[tuser.id].request()
        except BucketOverFull:
            # A warning was already given, fail silently
            log("Aborting compile due to `BucketOverfull`.", context=f"{ctx.msg.id}", level=logging.INFO)
            return None
        except BucketFull:
            log("Aborting compile due to `BucketFull`.", context=f"{ctx.msg.id}", level=logging.INFO)
            # Ratelimit warning
            await ctx.error_reply("Too many requests, please slow down!\n(You may try again in `5` seconds.)")
            return None

        # Retrieve the user lock, creating it if required
        if tuser.id not in self.user_locks:
            self.user_locks[tuser.id] = asyncio.Lock()

        async with self.user_locks[tuser.id]:
            # Don't compile if the bucket is already overfull
            if self.user_buckets[tuser.id].overfull:
                log("Aborting compile due to a newly overfull bucket.", context=f"{ctx.msg.id}", level=logging.INFO)
                return None

            # Compile the source
            error = await ctx.maketypst(self.source, tuser.id, preamble=self.preamble, colour=self.colour)

            # Obtain the output image path, potentially the failed image
            file_path_staged = AsyncPath(f"{staging_root}/{tuser.id}/{tuser.id}.png")
            exists = await file_path_staged.is_file()
            file_path = AsyncPath(failed_image_path) if not exists else file_path_staged

            # Force a consistent filename so the Components V2 `File` item
            # below can always reference `attachment://{filename}`, whether
            # this is the real output or the shared fallback image.
            filename = f"{tuser.id}.png"
            output_file = discord.File(file_path, filename=filename)

            view = TypstOutputView(
                source=self.source,
                error=error or None,
                image_filename=filename,
                author=ctx.author,
                header_name=self.header_name,
            )

            message: discord.Message | None = None
            try:
                message = await ctx.reply(file=output_file, view=view)
                view.message = message
            except discord.Forbidden:
                pass

            # purge storage if successful (no need for logs)
            if exists:
                cleanup_task = asyncio.ensure_future(self.cleanup_staging(tuser.id))
                self.ctx.tasks.append(cleanup_task)

        return message
