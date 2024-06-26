from .module import latex_module as module

from .core.LatexContext import LatexContext
from .core.LatexGuild import LatexGuild
from .core.LatexUser import LatexUser
from .core.tex_utils import ParseMode


@module.cmd(
    "tex",
    desc="Render LaTeX code.",
    aliases=["latex", "tikz", "lua", "luatex", "lualatex", "xelatex", "xetex"],
    flags=[
        "config",
        "keepsourcefor",
        "color",
        "colour",
        "alwaysmath",
        "allowother",
        "name",
    ],
)
async def cmd_tex(ctx, flags):
    """
    Usage``:
        {prefix}tex <code>
        {prefix}tikz <code>
        {prefix}luatex <code>
        {prefix}xetex <code>

    Description:
        Compiles and displays [LaTeX](https://www.overleaf.com/learn/latex/Learn_LaTeX_in_30_minutes) document code.\
            For a quick introduction to using LaTeX, see one of the resources linked below.

        The output is extensively configurable, see `{prefix}help texconfig` \
            for more information about the possible configuration options.

        LaTeX macros and packages may also be used in this command via \
            inclusion into the *preamble*, see `{prefix}help preamble` for more information.

        If a guild or user has *latex recognition* enabled (see `{prefix}config latex` and `{prefix}help autotex`), \
            messages containing LaTeX will automatically be compiled and this command \
            is generally not required.
    Aliases::
        tex: Code is compiled in the default `document` environment.
        tikz: Code is rendered in a `tikzpicture` environment.
        luatex: Code is compiled using LuaLaTeX engine.
        xetex: Code is compiled using XeLaTeX engine.
    Related:
        autotex, texconfig, preamble
    Examples``:
        {prefix}tex \\pdftexbanner
        {prefix}tikz \\draw(0,0) circle (1);
        {prefix}luatex \\luatexbanner
        {prefix}xetex \\the\\XeTeXversion\\XeTeXrevision
    """
    # Handle flags
    if any(flags.values()):
        return await ctx.error_reply(
            "LaTeX configuration has moved to the `texconfig` command.\n"
            "Please see `{}help texconfig` for usage.".format(ctx.best_prefix())
        )

    # Handle empty and erroneous input
    if ctx.alias == ",":
        if not ctx.args.strip(","):
            # We shouldn't respond to any number of ',' characters on their own.
            return
    elif not ctx.args:
        if ctx.alias == ",":
            # `,,` on its own might easily not be referring to us.
            return
        # else:
        #     return await ctx.error_reply(
        #         "Please give me something to compile, for example "
        #         "```latex\n"
        #         "{0}tex The solutions to \\(x^2 = 1\\) are \\(x = \\pm 1\\)."
        #         "```"
        #         "See `{0}help` and `{0}help tex` for detailed usage and further examples!".format(ctx.best_prefix())
        #     )

    # Handle `tex help`
    if ctx.args.lower() in ["help", "--help"]:
        return await ctx.error_reply(
            "Please use `{}help tex` for command help.".format(ctx.best_prefix())
        )

    # WARNING FOR BEGIN DOCUMET - REMOVED
    # if r"\begin{document}" in ctx.args or r"\documentclass" in ctx.args or r"\usepackage" in ctx.args:
    #     await ctx.error_reply(
    #         "I compile the code you give me by putting it into a template LaTeX document, between "
    #         "`\\begin{{document}}` and `\\end{{document}}` commands.\n"
    #         "Please don't give me code that belongs outside of there!\nSee `{prefix}help tex` for some examples "
    #         "of what I understand.\n\n"
    #         "**If you want to modify the template to add packages or your own macros, "
    #         "see `{prefix}help preamble`.**".format(prefix=ctx.best_prefix())
    #     )

    # Get latex user and guild
    lguild = LatexGuild.get(ctx.guild.id if ctx.guild else 0)
    luser = LatexUser.get(ctx.author.id)

    # Determine parse mode and flags
    flags = dict()
    parse_mode = 0

    # convert above if elif to match case
    match ctx.alias.lower():
        case "," | "mtex":
            parse_mode = ParseMode.GATHER
        case "align":
            parse_mode = ParseMode.ALIGN
        case "tikz":
            parse_mode = ParseMode.TIKZ
        case "texsp":
            flags["spoiler"] = True
        case "texw":
            flags["wide"] = True
        case _:
            parse_mode = ParseMode.DOCUMENT

    # Clean mentions
    content = ctx.clean_arg_str()

    # Parse source
    source = LatexContext.parse_content(content, parse_mode)

    if not source:
        return await ctx.error_reply(
            "Codeblocks found, but no LaTeX codeblocks!\n"
            "Please write your codeblocks as follows.\n"
            "\\`\\`\\`tex\ncode\n\\`\\`\\`"
        )

    match ctx.alias.lower():
        # Create latex context for a given context, source, guild, user and other flags
        # then compile LaTeX using a texcompile shell script of user's choice
        # then keep the command alive until the context dies
        case "lualatex" | "luatex" | "lua":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.luatexmake()
            await lctx.lifetime()

        case "xetex" | "xelatex":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.xetexmake()
            await lctx.lifetime()

        case _:
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.make()
            await lctx.lifetime()
