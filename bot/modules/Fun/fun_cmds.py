from contextlib import suppress

import discord
from cmdClient import Context  # noqa
from utils.lib import paginate_list

from .module import fun_module as module

"""
Some simple fun utility commands.

Commands provided:
    convertbinary:
        Translates a binary string to ascii
    lenny:
        Sends a lenny face
    sorry:
        Sends a sorry image
    discrim:
        Sends a list of users with matching discriminator
"""


@module.cmd("convertbinary", desc="Converts binary to text.")
async def cmd_convertbinary(ctx: Context):
    """
    Usage``:
        {prefix}convertbinary <binary string>
    Description:
        Converts the provided binary string into text.
    """
    bitstr = ctx.arg_str.replace(" ", "")
    if (not bitstr.isdigit()) or (len(bitstr) % 8 != 0):
        return await ctx.error_reply("Please provide a valid binary string!")
    bytelist = map("".join, zip(*[iter(bitstr)] * 8, strict=True))
    asciilist = [chr(sum([int(b) << 7 - n for (n, b) in enumerate(byte)])) for byte in bytelist]
    return await ctx.reply("Output: `{}`".format("".join(asciilist)))


@module.cmd("lenny", desc="( ͡° ͜ʖ ͡°)")
async def cmd_lenny(ctx: Context):
    """
    Usage``:
        {prefix}lenny
    Description:
        Sends lenny ( ͡° ͜ʖ ͡°).
    """
    with suppress(discord.Forbidden):
        await ctx.msg.delete()
    await ctx.reply("( ͡° ͜ʖ ͡°)")


@module.cmd("discrim", desc="Searches for users with a given discriminator.")
async def cmd_discrim(ctx: Context):
    """
    Usage``:
        {prefix}discrim [discriminator]
    Description:
        Searches all guilds the bot is in for users matching the given discriminator.
    """
    p = ctx.client.get_all_members()
    args = ctx.arg_str
    if (len(args) > 4) or not args.isdigit():
        await ctx.reply("You must give me at most four digits to find!")
        return
    discrim = "0" * (4 - len(args)) + args
    found_members = set(filter(lambda m: m.discriminator == discrim, p))
    if len(found_members) == 0:
        await ctx.reply("No users with this discriminator found!")
        return
    user_info = [(str(m), f"({m.id})") for m in found_members]
    max_len = len(max(list(zip(*user_info, strict=True))[0], key=len))
    user_strs = ["{0[0]:^{max_len}} {0[1]:^25}".format(user, max_len=max_len) for user in user_info]
    await ctx.pager(
        paginate_list(user_strs, title="{} user{} found".format(len(user_strs), "s" if len(user_strs) > 1 else "")),
    )


@module.cmd("sorry", desc="Sorry, love.")
async def cmd_sorry(ctx: Context):
    """
    Usage``:
        {prefix}sorry
    Description:
        Sorry, love.
    """
    try:
        embed = discord.Embed(color=discord.Colour.purple())
        embed.set_image(url="https://cdn.discordapp.com/attachments/309625872665542658/406040395462737921/image.png")
        await ctx.reply(embed=embed)
    except discord.Forbidden:
        return await ctx.error_reply("I lack the permission to send embeds here.")
    except Exception:
        pass
