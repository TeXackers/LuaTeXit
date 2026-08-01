import re

from cmdClient import Context
from cmdClient.lib import ResponseTimedOut

from .core.TypstUser import TypstUser, set_user_preamble
from .module import typst_module as module
from .resources import default_preamble

codeblock_re = re.compile(r"```(typst|typ)?", re.IGNORECASE)


@module.cmd(
    "typstpreamble",
    desc="View or modify your personal Typst preamble.",
    aliases=["tpreamble", "typreamble"],
    flags=["reset", "replace"],
)
async def cmd_typstpreamble(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}typstpreamble
        {prefix}typstpreamble --reset
        {prefix}typstpreamble --replace [code]
    Description:
        With no arguments or flags, displays the preamble used to compile your Typst.
        The flags may be used to modify or replace your preamble.
        This command supports file uploads, the contents of which are treated as [code].

        If [code] is provided without a flag, it replaces your preamble.

        Unlike the LaTeX preamble system, changes here take effect immediately --
        Typst has no shell-escape and packages come from a sandboxed registry, so
        there's no review queue.
    Flags::
        reset: Resets your preamble to the default.
        replace: Replaces your preamble with [code], or prompts for the new preamble.
    Related:
        typst
    """
    tuser = TypstUser.get(ctx.author.id)

    # Handle resetting the preamble
    if flags["reset"]:
        if tuser.preamble is None:
            return await ctx.error_reply("You don't have a custom Typst preamble to reset!")

        set_user_preamble(ctx.client, ctx.author.id, None)
        return await ctx.reply("Your Typst preamble has been reset to the default!")

    # Get any input, including the contents of any attached files if they exist
    if ctx.msg.attachments:
        attachment = ctx.msg.attachments[0]

        # If the file is over 1MB, it probably isn't a valid preamble.
        if attachment.size >= 1000000:
            return await ctx.error_reply("Attached file is too large to process (over `1MB`).")

        try:
            args = str(await attachment.read(), encoding="utf-8", errors="strict")
        except UnicodeError:
            return await ctx.error_reply("Couldn't decode the attached file, please ensure it uses the `utf-8` codec.")
    else:
        args = ctx.clean_arg_str()

    args = codeblock_re.sub("", args.strip()).strip()

    # Handle a request to replace the preamble
    if flags["replace"] or args:
        if not args:
            try:
                args = await ctx.on_input(
                    "Please enter your new preamble, or `c` to cancel.\n"
                    "**If you wish to upload a file as your preamble, "
                    "cancel now and rerun with the file attached.**",
                    timeout=600,
                )
            except ResponseTimedOut:
                return await ctx.error_reply("Query timed out, your preamble was not modified.")
            if args.lower() == "c":
                return await ctx.error_reply("Preamble replacement cancelled, your preamble was not modified.")
            args = codeblock_re.sub("", args.strip()).strip()

        set_user_preamble(ctx.client, ctx.author.id, args)
        return await ctx.reply("Your Typst preamble has been updated!")

    # If the user doesn't want to edit their preamble, they must just want to view it
    preamble = tuser.preamble or default_preamble
    header = "custom" if tuser.preamble else "default"
    title = f"{ctx.author.display_name}'s current Typst preamble ({header})"
    return await ctx.pager_v2(preamble, title=title, code=True, syntax="typst")
