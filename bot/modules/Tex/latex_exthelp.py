from .module import latex_module as module


async def latex_exthelp(ctx):
    await ctx.reply(
        f"Please see `{await ctx.best_prefix()}help tex` for help with the `tex` command. "
        "Extended documentation on LaTeX usage coming soon!",
    )


@module.init_task
def attach_latex_exthelp(client):
    pass
