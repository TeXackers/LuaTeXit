from cmdClient import Context
import random
import asyncio

from .module import fun_module as module


"""
Fun commands.

Commands provided:
    8ball:
        Ask the magic 8ball a question.
    roll:
        Roll a DND die.
"""

BALL: list[str] = [
    "As I see it, yes",
    "It is certain",
    "It is decidedly so",
    "Most likely",
    "Outlook good",
    "Signs point to yes",
    "Without a doubt",
    "Yes",
    "Yes – definitely",
    "You may rely on it",
    "Reply hazy, try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
    "Purrhaps :catthink:",
]

EMOJI: list[str] = ["🎱", "✨", "🔮", "🛐"]

DIESHAPES: dict[int, str] = {
    4: "🔺",
    6: "🎲",
    8: "🔷",
    10: "🔶",
    12: "🌟",
    20: "🔯",
    100: "🌕",
}


def parse_die(die: str) -> tuple[int, int]:
    """
    Parses a die string in the format [num]d[type], where num is optional and defaults to 1. Returns a tuple of (num, type) if successful, or None if the format is invalid.
    """
    if "d" not in die:
        raise ValueError(
            "Die must be in the format [num]d[type], where [num] is optional and defaults to 1."
        )
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


def generate_die_stats(rolls: list[int]):
    """
    Generate some descriptive statistics about a list of die rolls, such as the total, average, highest, and lowest rolls. Also generate a relevant statistical plot for the rolls, such as a histogram or box plot. Return the statistics and the plot as a string.
    """


@module.cmd(
    "8ball",
    desc="Ask the magic 8ball a question.",
    aliases=["8"],
)
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
        msg = await ctx.reply(f"{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 1.5))
        await msg.edit(content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 1.5))
        await msg.edit(
            content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}"
        )
        await asyncio.sleep(random.uniform(0.35, 1.5))
        await msg.edit(
            content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}"
        )
        await asyncio.sleep(random.uniform(0.35, 1.5))
        ballsays = random.choice(BALL)
        if ballsays == "Purrhaps :catthink:":
            await msg.edit(content=f"{ballsays}")
        else:
            await msg.edit(content=f"`{ballsays}`")
    else:
        await ctx.reply("That doesn't look like a question.")


@module.cmd(
    "roll",
    desc="Roll a DND die.",
    aliases=["die"],
)
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
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}"
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}"
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}"
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(content=rolls_str)
