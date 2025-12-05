import re

from wards import is_reviewer

from .core.LatexContext import LatexContext
from .core.LatexGuild import LatexGuild
from .core.LatexUser import LatexUser
from .core.tex_utils import ParseMode
from .module import latex_module as module


@module.cmd(
    "texas",
    desc="Render LaTeX code using an arbitrary person's configuration.",
    aliases=["pdfas", "luaas", "plainpdfas", "plainluaas", "xetexas"],
    flags=[
        "u="
    ]
)

@is_reviewer()
async def cmd_texas(ctx, flags):
    """
    Usage``:
        {prefix}texas -u <userid> <code>
        {prefix}luaas -u <userid> <code>
        {prefix}pdfas -u <userid> <code>

    Description:
        Similar to the `tex` command, but uses another user's LaTeX configuration, including their preamble. Default compilation method is LuaLaTeX.
    Examples``:
        {prefix}texas -u 1421147725335891981 \\luatexbanner
    """

    # we NEED the user flag
    if not flags["u"]:
        return await ctx.error_reply("You must specify a user with the `-u` flag.")

    # sometimes the value of the user flag might be invalid, like if it's not a number
    try:
        int(flags["u"])
    except ValueError:
        return await ctx.error_reply("The user ID provided is not valid. It must be set by a numeric Discord user ID.")

    # `texas help`
    if ctx.args.lower() in ("help", "--help"):
        return await ctx.error_reply(
            f"Please use `{ctx.best_prefix()}help texas` for detailed help on this command."
        )
    
    # Get latex user and guild
    lguild = LatexGuild.get(ctx.guild.id if ctx.guild else 0)
    luser = LatexUser.get(int(flags["u"]))

    parse_mode = ParseMode.DOCUMENT
    
    if luser.alwaysmath and parse_mode == ParseMode.DOCUMENT:
        parse_mode = ParseMode.GATHER
    
    # At the moment, this still has the `--user <userid>` or `-u <userid>` flag in it.
    content = ctx.clean_arg_str()
    
    # remove the flag
    content = re.sub(r'(--user|-u)\s+', '', content).strip()

    # remove the user ID using the flag dict
    content = content.replace(str(flags["u"]), '', 1).strip()
    
    # Parse source
    source = LatexContext.parse_content(
        content, parse_mode
    )
    
    if not source:
        return await ctx.error_reply("Codeblock is there, but you ought to specify `tex` or `latex` as the language.")

    # Since luser is the "as" user, force namestyle 4 (reaction-based)
    # Also pass the ID of the real user as mask_id
    luser.namestyle = 4
    target_id = str(flags["u"])
    
    match ctx.alias.lower():
        case "luaas" | "luatexas" | "lualatexas":
            lctx = LatexContext(ctx, source, lguild, luser, mask_id=target_id)
            await lctx.luatexmake()
            await lctx.lifetime()
        case "pdfas" | "pdftexas" | "pdflatexas":
            lctx = LatexContext(ctx, source, lguild, luser, mask_id=target_id)
            await lctx.make()
            await lctx.lifetime()
        case "xetexas" | "xelatexas":
            lctx = LatexContext(ctx, source, lguild, luser, mask_id=target_id)
            await lctx.xetexmake()
            await lctx.lifetime()
        case _:
            lctx = LatexContext(ctx, source, lguild, luser, mask_id=target_id)
            await lctx.luatexmake()
            await lctx.lifetime()