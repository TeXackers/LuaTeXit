import logging
import traceback

import discord
from cmdClient import Context, cmdClient  # noqa
from discord import Message
from logger import log

from .core.TypstContext import TypstContext
from .core.TypstGuild import TypstGuild
from .core.TypstUser import TypstUser
from .module import typst_module as module


async def typst_message_parser(client: cmdClient, message: Message):
    """
    Check incoming messages for a ```typst/```typ codeblock, render it if required,
    and add it to the context caches.
    As a cmdClient message parser, it handles both new messages and edits which were
    ignored by the command parser.
    """
    # Quit if module has been disabled
    if not module.enabled:
        return

    # Wait until module is ready
    await module.ready.wait()

    # Make sure there's content
    if not message.content:
        return

    # Bail out before touching clean_content/parse_content unless there's even a codeblock
    if "```" not in message.content:
        return

    # Get the typst guild
    lguild = TypstGuild.get(message.guild.id if message.guild else 0)

    # Check we can write in the channel and we're allowed to send images there
    if message.guild:
        my_permissions = message.channel.permissions_for(message.guild.me)
        if not (my_permissions.send_messages and my_permissions.attach_files):
            return

    # Build the potential typst source
    source = TypstContext.parse_content(message.clean_content)

    # If there's no source (e.g. everything is in a foreign codeblock) return immediately
    if not source:
        return

    # Only trigger on an explicitly typst/typ-labelled codeblock, not a bare ``` or
    # some other language -- unlike LaTeX's autotex, there's no weaker detection level.
    if not (("```typst\n" in message.content) or ("```typ\n" in message.content)):
        return

    # We are now in the (relatively rare) case that a message seems to have Typst.
    # Build the typst user
    tuser = TypstUser.get(message.author.id)

    # Check whether we are listening, now that we have everything
    if not (lguild.autotypst or tuser.autotypst):
        return

    # We have a valid piece of Typst, and we are listening for it. We may now compile.
    log(
        f"[ Typst ]\nusr: {message.author} ({message.author.id})\n"
        f"cid: {message.channel} ({message.channel.id})\n"
        f"gid: {message.guild or ''} ({message.guild.id if message.guild else ''})",
        context=f"mid:{message.id}",
    )

    # Create a context for the message and add it to the context caches
    ctx: Context = client.baseContext(client=client, message=message)
    client.ctx_cache[message.id] = ctx.flatten()
    client.active_contexts[message.id] = ctx

    try:
        tctx = TypstContext(ctx, source, tuser)
        await tctx.make()
    except discord.Forbidden:
        full_traceback = traceback.format_exc()
        log(
            f"Caught the following exception while rendering Typst.\n{full_traceback}",
            context=f"mid:{message.id}",
            level=logging.WARNING,
        )
    except Exception as e:
        full_traceback = traceback.format_exc()
        log(
            f"Caught the following exception while rendering Typst.\n{full_traceback}",
            context=f"mid:{message.id}",
            level=logging.ERROR,
        )
        raise
    else:
        log("AutoTypstCompile Success.", context=f"{message.id}", level=logging.DEBUG)
    finally:
        client.ctx_cache[message.id] = ctx.flatten()
        client.active_contexts.pop(message.id, None)


@module.init_task
def register_typst_parser(client: cmdClient):
    client.add_message_parser(typst_message_parser)


@module.cmd(
    "autotypst",
    desc="Toggle whether your Typst codeblocks are automatically rendered.",
    aliases=["typstlisten"],
)
async def cmd_autotypst(ctx: Context) -> None:
    """
    Usage``:
        {prefix}autotypst [on | off]
    Description:
        When used with no arguments, toggles your personal `autotypst` setting,
        that controls whether ```typst or ```typ codeblocks in your messages are
        automatically compiled.
    About automatic compilation:
        A ```typst/```typ codeblock will be automatically compiled when *either*
        your `autotypst` or the guild's `typst` setting are enabled.
    Related:
        typst, typstpreamble, typstconfig
    Examples``:
        {prefix}autotypst
        {prefix}autotypst on
        {prefix}autotypst off
    """
    tuser = TypstUser.get(ctx.author.id)

    largs = ctx.args.lower()

    if largs and largs not in ("on", "off"):
        return await ctx.error_reply(f"Unrecognised option `{largs}`.\nPlease use `on` or `off`.")

    if largs == "off" or (not largs and tuser.autotypst):
        tuser.settings["autotypst"].save(ctx.client, ctx.author.id, False)
        return await ctx.reply(
            "You have *disabled* personal automatic Typst compilation.\n"
            "Please be aware that Typst codeblocks will still be rendered in guilds "
            "with the `typst` setting enabled.",
        )

    tuser.settings["autotypst"].save(ctx.client, ctx.author.id, True)
    return await ctx.reply(
        "You have *enabled* personal automatic Typst compilation.\n"
        "I will now compile any ```typst or ```typ codeblock in your messages.\n"
        "Please be aware that automatic compilation may be restricted by guild settings.",
    )
