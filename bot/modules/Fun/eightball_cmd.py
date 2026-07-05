import asyncio
import random

import discord
from cmdClient import Context, Layouts
from discord import Colour

from .module import fun_module as module

"""
Fun commands.

Commands provided:
    8ball:
        Ask the magic 8ball a question.
    roll:
        Roll a DND die.
"""

BALL_GIF: str = "https://1b-f.s3.eu-west-1.amazonaws.com/a/66430-C5FEC1C6-5F69-4576-A1F1-097BE9258E3E-0-1482505335.gif"

BALL: list[str] = [
    "It is certain",  # b
    "It is decidedly so",  # b
    "Without a doubt",  # b
    "Yes – definitely",  # b
    "You may rely on it",  # b
    "As I see it, yes",  # g
    "Most likely",  # g
    "Outlook good",  # g
    "Signs point to yes",  # g
    "Yes",  # g
    "Reply hazy, try again",  # y
    "Ask again later",  # y
    "Better not tell you now",  # y
    "Cannot predict now",  # y
    "Concentrate and ask again",  # y
    "Purrhaps :catthink:",  # y
    "Don't count on it",  # r
    "My reply is no",  # r
    "My sources say no",  # r
    "Outlook not so good",  # r
    "Very doubtful",  # r
]

col_megapositive: Colour = Colour.from_rgb(0, 0, 150)
col_positive: Colour = Colour.from_rgb(0, 150, 0)
col_uncertain: Colour = Colour.from_str("0xFFA107")
col_negative: Colour = Colour.from_rgb(150, 0, 0)

BALL_COLOURS: list[Colour] = 5 * [col_megapositive] + 5 * [col_positive] + 6 * [col_uncertain] + 5 * [col_negative]

EMOJI: list[str] = ["🎱", "✨", "🔮", "🛐"]


@module.cmd("8ball", desc="Ask the magic 8ball a question.", aliases=["8"])
async def cmd_8ball(ctx: Context):
    """
    Usage``:
        {prefix}8ball <question>
    Description:
        Ask the magic 8ball a question. Question must end with a question mark.
    """
    if ctx.arg_str.endswith("?") and ctx.arg_str != "?":
        # reply with random emojis with random sleep time first
        # emoji selection: 🎱, ✨, 🔮, 🛐
        # then edit the message with the 8ball response

        # animation
        anim_msg = await ctx.reply(f"{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 0.95))
        await anim_msg.edit(content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 0.95))
        await anim_msg.edit(content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 0.95))
        await anim_msg.edit(
            content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}",
        )
        await asyncio.sleep(random.uniform(0.35, 0.95))
        ballsays = random.choice(BALL)

        await anim_msg.delete()
        return await ctx.reply(
            view=Layouts.GenericFullEmbed(
                f"{ctx.arg_str}",
                ballsays,
                f"{discord.utils.format_dt(discord.utils.utcnow(), 'F')}",
                BALL_GIF,
                BALL_COLOURS[BALL.index(ballsays)],
            ),
        )
    return await ctx.error_reply("That doesn't look like a question.")
