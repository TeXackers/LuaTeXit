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

DIESHAPES: dict[int, str] = {4: "🔺", 6: "🎲", 8: "🔷", 10: "🔶", 12: "🌟", 20: "🔯", 100: "🌕"}


def parse_die(die: str) -> tuple[int, int]:
    """
    Parses a die string in the format [num]d[type], where num is optional and defaults to 1. Returns a tuple of (num, type) if successful, or None if the format is invalid.
    """
    if "d" not in die:
        raise ValueError("Die must be in the format [num]d[type], where [num] is optional and defaults to 1.")
    num_str, type_str = die.split("d", 1)
    if num_str == "":
        num = 1
    else:
        if not num_str.isdigit():
            raise ValueError("The number of dice must be a number.")
        num = int(num_str)
    # prevent abuse by limiting the number of dice that can be rolled at once
    if num < 1 or num > 20:
        raise ValueError("You can only roll between 1 and 20 dice at once.")
    if not type_str.isdigit():
        raise ValueError("Die type must be a number.")
    type_ = int(type_str)
    if type_ not in [4, 6, 8, 10, 12, 20, 100]:
        raise ValueError("Invalid die type. Valid types are: 4, 6, 8, 10, 12, 20, 100.")
    return (num, type_)


@module.cmd("8ball", desc="Ask the magic 8ball a question.", aliases=["8"])
async def cmd_8ball(ctx):
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
            content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}"
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
            )
        )
    return await ctx.error_reply("That doesn't look like a question.")


@module.cmd("roll", desc="Roll a DND die.", aliases=["die"])
async def cmd_roll(ctx: Context):
    """
    Usage``:
        {prefix}roll <die>
    Description:
        Roll a DND die. Example: `d20`, `2d6`.
    """

    # Die types: 4, 6, 8, 10, 12, 20, 100
    # Format: [num]d[type], num is optional and defaults to 1
    # The printed output:
    # for every die rolled, print the prepend emoji then the result. Every roll is on a new line. If multiple dice are rolled, print the total at the end, using "✏️" as the prepend emoji.

    # use try catch to handle invalid die format
    try:
        num, type_ = parse_die(ctx.arg_str)
    except ValueError as e:
        return await ctx.error_reply(str(e))

    rolls = [random.randint(1, type_) for _ in range(num)]
    total = sum(rolls)
    shape = DIESHAPES[type_]
    rolls_str = "\n".join(f"{shape} {roll}" for roll in rolls)

    if num > 1:
        rolls_str += f"\n-# ✏️ Total: `{total}`"

    # animation (similar to 8ball above but from the dict.values() of the die type)
    random_shapes = list(DIESHAPES.values())
    msg = await ctx.reply(f"{random.choice(random_shapes)}")
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}")
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}"
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}"
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    return await msg.edit(content=rolls_str)
