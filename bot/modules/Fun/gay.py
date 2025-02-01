import discord
from cmdClient import Context
from utils.lib import paginate_list
import random
import asyncio

from .module import fun_module as module


"""
Fun commands.

Commands provided:
    8ball:
        Ask the magic 8ball a question.
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
        await msg.edit(content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 1.5))
        await msg.edit(content=f"{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}{random.choice(EMOJI)}")
        await asyncio.sleep(random.uniform(0.35, 1.5))
        ballsays = random.choice(BALL)
        if ballsays == "Purrhaps :catthink:":
            await msg.edit(content=f"{ballsays}")
        else:
            await msg.edit(content=f"`{ballsays}`")
    else:
        await ctx.reply("That doesn't look like a question.")
    