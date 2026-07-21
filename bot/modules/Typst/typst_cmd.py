from cmdClient import Context  # noqa

from .core.TypstContext import TypstContext
from .module import typst_module as module


@module.cmd(
    "typst",
    desc="Render Typst code.",
    aliases=["typ"],
)
async def cmd_typst(ctx: Context):
    """
    Usage``:
        {prefix}typst <code>
    Description:
        Compiles and displays [Typst](https://typst.app/docs) document code.

        Typst macros and packages may also be used via inclusion into your personal
        *preamble*, see `{prefix}help typstpreamble` for more information.
    Related:
        typstpreamble
    Examples``:
        {prefix}typst Hello $x^2 + y^2 = z^2$ world!
    """
    if not ctx.args:
        return await ctx.error_reply(
            "Please give me something to compile, for example "
            "```typst\n"
            f"{await ctx.best_prefix()}typst Hello $x^2 + y^2 = z^2$ world!"
            "```"
            f"See `{await ctx.best_prefix()}help typst` for detailed usage and further examples!",
        )

    content = ctx.clean_arg_str()

    source = TypstContext.parse_content(content)

    if not source:
        return await ctx.error_reply(
            "Codeblocks found, but no Typst codeblocks!\n"
            "Please write your codeblocks as follows.\n"
            "\\`\\`\\`typst\ncode\n\\`\\`\\`",
        )

    tctx = TypstContext(ctx, source)
    await tctx.make()
    return None
