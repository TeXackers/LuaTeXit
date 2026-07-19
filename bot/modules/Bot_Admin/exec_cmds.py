import asyncio
import sys
import traceback
from io import StringIO
from typing import TYPE_CHECKING

from cmdClient import Context  # noqa
from wards import is_dev, is_owner

from .module import bot_admin_module as module

if TYPE_CHECKING:
    from discord import Message

"""
Exec level commands to manage the bot.
All commands require master permission.

Commands provided:
    async:
        Executes provided code in an async executor.
    exec:
        Executes code using standard python exec.
    eval:
        Executes code and awaits it if required.
    shell:
        Runs a command in the executing environment
"""


async def _reply_code_result(ctx: Context, label: str, code: str, output: str, error: int) -> Message:
    """
    Reply with the `code` that was run and its `output`.

    Falls back to a paginator if the formatted message would exceed Discord's message limit.
    """

    return await ctx.pager_v2(
        str(output),
        title=f"{label} output" + (" (error)" if error else ""),
        code=True,
        syntax="py",
        maxheight=25,
    )


@module.cmd("async", desc="Executes async code and displays the output.")
@is_dev()
async def cmd_async(ctx: Context) -> Message | None:
    """
    Usage``:
        {prefix}async <code>
    Description:
        Runs `<code>` as an asynchronous coroutine and prints the output or error.

        *Requires you to be a developer of the bot.*
    """
    if not ctx.arg_str:
        return await ctx.error_reply("You must give me something to run!")

    output, error = await _async(ctx)
    if not error and not output:
        return None
    return await _reply_code_result(ctx, "Async", ctx.arg_str, output, error)


@module.cmd("exec", desc="Executes python code using exec and displays the output.")
@is_owner()
async def cmd_exec(ctx: Context) -> Message | None:
    """
    Usage``:
        {prefix}exec <code>
    Description:
        Runs `<code>` in current environment using exec() and prints the output or error.

        *Requires you to be an owner of the bot.*
    """
    if not ctx.arg_str:
        return await ctx.error_reply("You must give me something to run!")

    output, error = await _exec(ctx)
    if not error and not output:
        return None
    return await _reply_code_result(ctx, "Exec", ctx.arg_str, output, error)


@module.cmd("eval", desc="Executes python code using eval and displays the output.", flags=["s"])
@is_owner()
async def cmd_eval(ctx: Context, flags) -> Message | None:
    """
    Usage``:
        {prefix}eval <code> [-s]
    Description:
        Runs `<code>` in current environment using `eval()` and prints the output or error.

        *Requires you to be an owner of the bot.*
    Flags::
        s: Eval silently and don't print any output unless there is an error.
    """
    if not ctx.arg_str:
        return await ctx.error_reply("You must give me something to run!")

    output, error = await _eval(ctx)
    if not error and not output:
        return None
    if not flags["s"] or error:
        return await _reply_code_result(ctx, "Eval", ctx.args, output, error)
    return None


@module.cmd("shell", desc="Runs a command in the operating environment.")
@is_owner()
async def cmd_shell(ctx: Context) -> Message | None:
    """
    Usage``:
        {prefix}shell <command>
    Description:
        Runs `<command>` in the operating environment and returns the output in a codeblock.
    """
    if not ctx.arg_str:
        return await ctx.error_reply("You must give me something to run!")

    output = await ctx.run_in_shell(ctx.arg_str) or "No output."
    return await ctx.pager_v2(
        output,
        title=f"Command output for:\n```sh\n$ {ctx.arg_str}\n```",
        code=True,
        syntax="python",
        maxheight=25,
    )


async def _eval(ctx: Context):
    output = None
    try:
        output = eval(ctx.args)  # noqa
    except Exception:
        return (str(traceback.format_exc()), 1)
    if asyncio.iscoroutine(output):
        output = await output
    return (output, 0)


async def _exec(ctx: Context):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    try:
        exec(ctx.args)  # noqa
        result = (redirected_output.getvalue(), 0)
    except Exception:
        result = (str(traceback.format_exc()), 1)
    finally:
        sys.stdout = old_stdout
    return result


async def _async(ctx: Context):
    env: dict[str, object] = {"ctx": ctx}
    env.update(globals())
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    exec_string = "async def _temp_exec():\n"
    exec_string += "\n".join(" " * 4 + line for line in ctx.args.split("\n"))
    try:
        exec(exec_string, env)  # noqa
        result = (redirected_output.getvalue(), 0)
    except Exception:
        return (str(traceback.format_exc()), 1)
    _temp_exec = env["_temp_exec"]
    try:
        returnval = await _temp_exec()
        value = redirected_output.getvalue()
        result = (value, 0) if returnval is None else (value + "\n" + str(returnval), 0)
    except Exception:
        result = (str(traceback.format_exc()), 1)
    finally:
        sys.stdout = old_stdout
    return result
