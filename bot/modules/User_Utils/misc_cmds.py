import string
from contextlib import suppress

import aiohttp
import discord
from cmdClient import Context  # noqa
from utils.lib import prop_tabulate, split_text
from wards import in_guild

from .module import utils_module as module


@module.cmd("echo", desc="Sends what you tell me to!")
async def cmd_echo(ctx: Context):
    """
    Usage``:
        {prefix}echo <text>
    Description:
        Replies to the message with `text`.

        (Note: This command may be disabled with `{prefix}disablecmd echo`.)
    """
    return await ctx.reply(discord.utils.escape_mentions(ctx.args) if ctx.args else "I can't send an empty message!")


@module.cmd("secho", desc="Deletes your message and echos it.")
async def cmd_secho(ctx: Context):
    """
    Usage``:
        {prefix}secho <text>
    Description:
        Replies to the message with `text` and deletes your message.

        (Note: This command may be disabled with `{prefix}disablecmd secho`.)
    """
    try:
        if ctx.args:
            await ctx.msg.delete()
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass

    await ctx.reply(discord.utils.escape_mentions(ctx.args) if ctx.args else "I can't send an empty message!")


@module.cmd("jumpto", desc="Finds the given messageid and generates a jump link.")
@in_guild()
async def cmd_jumpto(ctx: Context):
    """
    Usage``:
        {prefix}jumpto <msgid>
    Description:
        Searches for the given `msgid` amongst all the guild channels you can see, then replies with the jump link.
    Examples``:
        {prefix}jumpto {ctx.msg.id}
    """

    msgid = ctx.args
    if not msgid or not msgid.isdigit():
        await ctx.error_reply("Please provide a valid message ID.")
        return
    msgid = int(msgid)

    # Placeholder output
    embed = discord.Embed(
        colour=discord.Colour.green(),
        description="Searching for message {}".format(ctx.client.conf.emojis.getemoji("loading")),
    )
    out_msg = await ctx.reply(embed=embed)

    # Try looking in the current channel first
    message = None
    try:
        message = await ctx.ch.fetch_message(msgid)
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass

    if message is None:
        # A more thorough seek is required
        message = await ctx.find_message(msgid, ignore=[ctx.ch.id])

    if message is None:
        embed.description = "Couldn't find the message!"
        embed.colour = discord.Colour.red()
    else:
        embed.description = f"[Jump to message]({message.jump_url})"

    try:
        await out_msg.edit(embed=embed)
    except discord.NotFound:
        await ctx.reply(embed=embed)


@module.cmd("quote", desc="Quotes a message by ID.", flags=["a", "r"])
@in_guild()
async def cmd_quote(ctx: Context, flags: dict[str, bool]):
    """
    Usage``:
        {prefix}quote <messageid> [-a] [-r]
    Description:
        Searches for the given `messageid` amongst messages in channels (of the current guild) that you can see, \
            and forwards the desired message to the current channel.
    Flags::
        -a: (anonymous) Removes author information from the quote embed if `-r` is also used.
        -r: (raw) The message content is instead displayed in a codeblock, to show any markdown.
    Examples``:
        {prefix}quote {ctx.msg.id}
    """
    error_msg = "Please provide a valid message ID."
    if not ctx.args:
        return await ctx.error_reply(error_msg)
    msgid = ctx.args.split()[0]
    if not msgid.isdigit():
        return await ctx.error_reply(error_msg)
    msgid = int(msgid)

    # Placeholder output
    embed = discord.Embed(
        colour=discord.Colour.green(),
        description="Searching for message {}".format(ctx.client.conf.emojis.getemoji("loading")),
    )
    out_msg = await ctx.reply(embed=embed)

    # Try looking in the current channel first
    message = None
    try:
        message = await ctx.ch.fetch_message(msgid)
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass

    if message is None:
        # A more thorough seek is required
        message = await ctx.find_message(msgid, ignore=[ctx.ch.id])

    if message is None:
        embed.description = "Couldn't find the message!"
        embed.colour = discord.Colour.red()
        try:
            out_msg = await out_msg.edit(embed=embed)
        except discord.NotFound:
            await ctx.reply(embed=embed)

    # Anonymous flag has no impact on the forwarding format, only allow use if raw is also being used.
    if flags["a"] and not flags["r"]:
        embed.description = (
            "The `-a` (anonymous) flag cannot be used by itself.\nPlease use it alongside the `-r` (raw) flag."
        )
        embed.colour = discord.Colour.red()
        try:
            out_msg = await out_msg.edit(embed=embed)
        except discord.NotFound:
            await ctx.reply(embed=embed)

    elif not flags["r"]:
        embed.description = "Failed to forward the message. Please try again."
        embed.colour = discord.Colour.red()

        # Delete the output embed as forwarded messages can't go in there
        with suppress(discord.NotFound):
            out_msg = await out_msg.delete()

        # Forward message to current channel
        try:
            await message.forward(ctx.ch)
        except discord.HTTPException:
            await out_msg.edit(embed=embed)

    else:
        quote_content = message.content.replace("```", "[CODEBLOCK]")

        header = f"[Click to jump to message]({message.jump_url})"
        blocks = split_text(quote_content, 1000, code=flags["r"])

        embeds = []
        for block in blocks:
            desc = header + "\n" + block if message.content else header + "\n"

            embed = discord.Embed(colour=discord.Colour.light_grey(), description=desc, timestamp=message.created_at)

            if not flags["a"]:
                embed.set_author(name=f"{message.author.name}", icon_url=message.author.display_avatar)
            embed.set_footer(text=f"Sent in #{message.channel.name}")
            if message.attachments:
                embed.set_image(url=message.attachments[0].proxy_url)
            embeds.append(embed)

        try:
            if len(embeds) == 1:
                out_msg = await out_msg.edit(embed=embeds[0])
            else:
                out_msg = await out_msg.delete()
                await ctx.pager(embeds, locked=False)
        except discord.NotFound:
            await ctx.pager(embeds, locked=False)


@module.cmd("invitebot", desc="Generates a bot invite link for a given bot or botid.", aliases=["ibot"])
async def cmd_invitebot(ctx: Context):
    """
    Usage``:
        {prefix}invitebot <bot>
    Description:
        Replies with an invite link for the bot.
        `bot` must be an id or a partial name or mention.
    Examples``:
        {prefix}invitebot {ctx.author.display_name}
    """
    user = None
    userid = None

    if ctx.args.isdigit():
        userid = int(ctx.args)
    elif ctx.guild:
        user = await ctx.find_member(ctx.args, interactive=True)
        if not user:
            return None
        userid = user.id
    else:
        return ctx.error_reply("Please supply a bot client id to get the invite link for.")

    invite_link = f"<https://discordapp.com/api/oauth2/authorize?client_id={userid}&permissions=0&scope=bot>"

    if userid == ctx.author.id:
        return await ctx.reply("Hey, do you want to come hang out?")

    if userid == ctx.client.user.id:
        return await ctx.reply(
            "Sure, I would love to!\n"
            "My official invite link is: {}\n"
            "If you don't want to invite me with my usual permissions, you can also use:\n"
            "{}".format(ctx.client.app_info["invite_link"], invite_link),
        )

    if user is not None and not user.bot:
        return await ctx.reply("Maybe you could try asking them nicely?")

    return await ctx.reply(f"Permissionless invitelink for `{userid}`:\n{invite_link}")


@module.cmd("colour", desc="Displays information about a colour.", aliases=["color"])
async def cmd_colour(ctx: Context):
    """
    Usage``:
        {prefix}colour <hexvalue>
    Description:
        Displays some detailed information about the colour, including a picture.
    Examples``:
        {prefix}colour #0047AB
        {prefix}colour 0047AB
    """
    hexstr: str = ctx.args.strip("#")
    if not (len(hexstr) == 6 and all(c in string.hexdigits for c in hexstr)):
        return await ctx.error_reply("Please give me a valid hex colour (e.g. #0047AB)")
    fetchstr = f"https://www.thecolorapi.com/id?hex={hexstr}"
    async with aiohttp.ClientSession() as session, session.get(fetchstr) as r:
        if r.status == 200:
            js = await r.json()
            inverted = col_invert(hexstr)
            prop_list = ["rgb", "hsl", "hsv", "cmyk", "XYZ"]
            value_list = [js[prop]["value"][len(prop) :] for prop in prop_list]
            desc = prop_tabulate(prop_list, value_list)
            embed = discord.Embed(
                title=f"Colour info for `#{hexstr}`",
                color=discord.Colour(int(hexstr, 16)),
                description=desc,
            )
            embed.set_thumbnail(url=f"http://placehold.it/150x150.png/{hexstr}/{inverted}?text=%23{hexstr}")
            embed.add_field(
                name="Closest named colour",
                value=f"`{js['name']['value']}` (Hex `{js['name']['closest_named_hex']}`)",
            )
            return await ctx.reply(embed=embed)
        return await ctx.error_reply("Sorry, something went wrong while fetching your colour! Please try again later")


def col_invert(color_to_convert):
    table = str.maketrans("0123456789abcdef", "fedcba9876543210")
    return color_to_convert.lower().translate(table).upper()
