import asyncio
import random

from cmdClient import Context

from .module import fun_module as module

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
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}",
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    await msg.edit(
        content=f"{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}{random.choice(random_shapes)}",
    )
    await asyncio.sleep(random.uniform(0.35, 1.15))
    return await msg.edit(content=rolls_str)
