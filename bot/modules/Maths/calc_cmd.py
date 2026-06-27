import json

import aiohttp
import discord
from cmdClient import Context  # noqa

from .module import maths_module as module

"""
Provides the calc command
"""

API_ADDR = "http://api.mathjs.org/v4/"


@module.cmd("calc", desc="Calculate short mathematical expressions.")
async def cmd_calc(ctx: type[Context]):
    """
    Usage``:
        {prefix}calc <expr>
    Description:
        Calculates the provided expressions and returns the result.

        Multiple expressions may be entered simultaneously, separated by newlines.
        Variables defined in one expression will be remembered in the expressions below.

        For further documentation see the [mathjs API docs](http://api.mathjs.org/).
    Examples``:
        {prefix}calc sin(45 deg)
        {prefix}calc det([1, 1; 2, 3])
        {prefix}calc 5 inches to cm
    """
    if not ctx.args:
        return await ctx.error_reply(
            f"Please give me something to evaluate.\nSee `{ctx.best_prefix()}help calc` for usage details."
        )
    exprs = ctx.args.split("\n")
    request = {"expr": exprs, "precision": 14}
    async with aiohttp.ClientSession() as session, session.post(API_ADDR, data=json.dumps(request)) as resp:
        answer = await resp.json()
    if "error" not in answer or "result" not in answer:
        return await ctx.error_reply(
            "Sorry, could not complete your request.\nAn unknown error occurred during calculation!"
        )
    if answer["error"]:
        await ctx.reply(
            "The following error occured while calculating:\n`{}`".format(
                discord.utils.escape_mentions(answer["error"])
            )
        )
        return None
    return await ctx.reply(
        "Result{}:\n```\n{}\n```\n-# Requested by: {}".format(
            "s" if len(exprs) > 1 else "", "\n".join(answer["result"]), ctx.author
        )
    )
