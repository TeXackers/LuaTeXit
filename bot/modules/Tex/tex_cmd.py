from cmdClient import Context  # noqa

from .core.LatexContext import LatexContext
from .core.LatexGuild import LatexGuild
from .core.LatexUser import LatexUser
from .core.tex_utils import ParseMode
from .module import latex_module as module
from wards import is_dev


@module.cmd(
    "tex",
    desc="Render LaTeX code.",
    aliases=[
        "pdftex",
        "pdf",
        "tikz",
        "lua",
        "luatex",
        "lualatex",
        "xelatex",
        "xetex",
        "plainpdf",
        "plainlua",
        "gather",
        "align",
        "texsp",
        "texw",
        "mtex",
        "pytex",
        "python",
    ],
    flags=["config", "keepsourcefor", "color", "colour", "alwaysmath", "allowother", "name"],
)
async def cmd_tex(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}luatex <code>
        {prefix}pdftex <code>
        {prefix}xetex <code>
        {prefix}plainlua <code>
        {prefix}plainpdf <code>
        {prefix}pytex <code>
        {prefix}tikz <code>

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
        luatex: Code is compiled using LuaLaTeX.
        pdftex: Code is compiled using pdfLaTeX.
        xetex: Code is compiled using XeLaTeX.
        plainlua: Code is compiled using plain LuaTeX.
        plainpdf: Code is compiled using plain pdfTeX.
        pytex: Code is compiled using LuaLaTeX + pythonTeX.
        tikz: Code is rendered in a `tikzpicture` environment using LuaLaTeX.
    Related:
        autotex, texconfig, preamble
    Examples``:
        {prefix}luatex \\luatexbanner
        {prefix}pdftex \\pdftexbanner
        {prefix}tikz \\draw(0,0) circle (1);
        {prefix}xetex \\the\\XeTeXversion\\XeTeXrevision
        {prefix}plainlua \\luatexbanner
        {prefix}plainpdf \\pdftexbanner
        {prefix}pytex \\py{{2+2}}
    """
    # Handle flags
    if any(flags.values()):
        return await ctx.error_reply(
            "LaTeX configuration has moved to the `texconfig` command.\n"
            f"Please see `{await ctx.best_prefix()}help texconfig` for usage.",
        )

    # Handle empty and erroneous input
    if ctx.alias == "," and not ctx.args.strip(","):
        # We shouldn't respond to any number of ',' characters on their own.
        return None
    if not ctx.args and ctx.alias == ",":
        # `,,` on its own might easily not be referring to us.
        return None
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
        return await ctx.error_reply(f"Please use `{await ctx.best_prefix()}help tex` for command help.")

    # warning for code that belongs outside of the document environment
    # but skip if the author is a dev
    has_document_code = r"\begin{document}" in ctx.args or r"\documentclass" in ctx.args or r"\usepackage" in ctx.args
    if has_document_code and not await is_dev.run(ctx):
        prefix: str = await ctx.best_prefix()
        return await ctx.error_reply(
            "I compile the code you give me by putting it into a template LaTeX document, between "
            "`\\begin{document}` and `\\end{document}` commands.\n"
            f"Please don't give me code that belongs outside of there!\nSee `{prefix}help tex` for some examples "
            "of what I understand.\n\n"
            "**If you want to modify the template to add packages or your own macros, "
            f"see `{prefix}help preamble`.**"
        )

    # Get latex user and guild
    lguild = LatexGuild.get(ctx.guild.id if ctx.guild else 0)
    luser = LatexUser.get(ctx.author.id)

    # Determine parse mode and flags
    flags: dict[str, bool] = {}
    parse_mode = ParseMode.DOCUMENT

    # convert above if elif to match case
    match ctx.alias.lower():
        case "," | "mtex" | "gather":
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
            pass

    # alwaysmath
    if luser.alwaysmath and parse_mode == ParseMode.DOCUMENT:
        parse_mode = ParseMode.GATHER

    # Clean mentions
    content = ctx.clean_arg_str()

    # Parse source
    source = LatexContext.parse_content(content, parse_mode)

    if not source:
        return await ctx.error_reply(
            "Codeblocks found, but no LaTeX codeblocks!\n"
            "Please write your codeblocks as follows.\n"
            "\\`\\`\\`tex\ncode\n\\`\\`\\`",
        )

    match ctx.alias.lower():
        # Create latex context for a given context, source, guild, user and other flags
        # then compile LaTeX using a texcompile shell script of user's choice
        # then keep the command alive until the context dies
        case "lua" | "luatex" | "lualatex":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.luatexmake()
            await lctx.lifetime()

        case "pdf" | "pdftex" | "pdflatex":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.make()
            await lctx.lifetime()

        case "xetex" | "xelatex":
            return await ctx.error_reply(
                "Xe(La)TeX support has been temporarily disabled.\nPlease use LuaLaTeX or pdfLaTeX instead.\n",
            )

        case "plainlua":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.plain_luatex_make()
            await lctx.lifetime()

        case "plainpdf" | "pdfplain":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.plain_pdftex_make()
            await lctx.lifetime()

        case "pytex" | "python":
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.pythontexmake()
            await lctx.lifetime()

        case _:
            lctx = LatexContext(ctx, source, lguild, luser, **flags)
            await lctx.luatexmake()
            await lctx.lifetime()
    return None
