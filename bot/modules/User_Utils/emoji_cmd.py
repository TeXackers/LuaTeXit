import asyncio
import datetime

import aiohttp
import discord
from cmdClient import cmdClient
from discord.http import Route
from utils.lib import prop_tabulate, strfdelta

from .module import utils_module as module

emoji_url = "https://cdn.discordapp.com/emojis/{id}.{img_type}"


async def get_custom_emoji(ctx, guild_id, emoji_id):
    emoji = await ctx.client.http.request(
        Route(
            "GET",
            "/guilds/{guild_id}/emojis/{emoji_id}".format(
                guild_id=guild_id, emoji_id=emoji_id
            ),
        )
    )
    return emoji


async def get_custom_emojis(ctx, guild_id):
    emojis = await ctx.client.http.request(
        Route("GET", "/guilds/{guild_id}/emojis".format(guild_id=guild_id))
    )
    return emojis


async def emoji_validity(emoji):
    """
    Check the validity of emoji['id'] by attempting to get it from discord.
    Also set the animated field if not set.
    """
    if "id" not in emoji:
        return None

    # Try to get the animated version
    async with aiohttp.ClientSession() as session:
        async with session.get(emoji_url.format(id=emoji["id"], img_type="gif")) as r:
            await r.read()  # To silence a exception caused by a bug with aiohttp and python3.7
            if r.status == 200:
                emoji["animated"] = True
                return True

        # Try to get the static version
        async with session.get(emoji_url.format(id=emoji["id"], img_type="png")) as r:
            await r.read()  # To silence a exception caused by a bug with aiohttp and python3.7
            if r.status == 200:
                emoji["animated"] = False
                return True

    # Neither version worked, the emoji is invalid
    return False


def read_emoji_link(emoji):
    """
    Return an image url for this emoji, accounting for animated setting.
    """
    return emoji_url.format(
        id=emoji["id"], img_type="gif" if emoji.get("animated", False) else "png"
    )


@module.cmd(
    "emoji",
    desc="Displays info about, searches for, and enlarges custom emojis",
    aliases=["e", "ee", "ree", "sree", "emote"],
    flags=["e", "to==", "up=="],
)
async def cmd_emoji(ctx: cmdClient, flags):
    """
    Usage``:
        {prefix}emoji <emoji> [-e]
        {prefix}ee <emoji>
        {prefix}ree <emoji>  [--to msgid | --up count]
        {prefix}sree <emoji>
    Description:
        Displays some information about the provided custom emoji, and sends an enlarged version.
        If the emoji isn't found, instead searches for the emoji amongst all the emojis I can see.
        If used as ee or given with -e flag, only shows the enlarged image.
        If used as ree, reacts with the emoji, and as sree, silently reacts.
        Built in emoji support is coming soon!
    Flags::
        ​e: Only shows the enlarged emoji, with no other information.
        to: Accepts a message id in the current channel to react to.
        up: Accepts a number of messages above yours to react to (default is `1`).
    Examples``:
        {prefix}e catThink
    """
    prefix = ctx.best_prefix()

    # Flags indicating what we want to do
    react_only = ctx.alias in ["ree", "sree"]
    enlarged_only = (ctx.alias == "ee") or (flags["e"] and not react_only)
    info = (ctx.alias == "emoji") and not enlarged_only

    if not (ctx.args or react_only):
        # If no arguments are given and we aren't reacting, just list the current guild custom emojis.
        if not ctx.guild:
            await ctx.error_reply(
                "Search for emojis using `{}emoji <emojistring>`".format(prefix)
            )
        else:
            emojis = ctx.guild.emojis
            if not emojis:
                await ctx.error_reply(
                    "No custom emojis found in this guild!\n"
                    "Use this command to search for custom emojis from my other guilds."
                )
            else:
                emojistrs = [
                    "{}`{id}` {name}".format(str(e), id=e.id, name=e.name)
                    for e in emojis
                ]
                blocks = [
                    "\n".join(emojistrs[i : i + 10])
                    for i in range(0, len(emojistrs), 10)
                ]
                embeds = [
                    discord.Embed(
                        title="Custom emojis in this guild",
                        description=block,
                        colour=discord.Colour.light_grey(),
                        timestamp=datetime.datetime.now(),
                    )
                    for block in blocks
                ]
                await ctx.pager(embeds, locked=False)
        return

    # If there's no args now that means we're reacting, and default reaction is reeeeeee
    em_str = ctx.args.lower().strip(":") or "reeeeeeeeeee"

    # Time to find the emoji.
    emoji = None  # The found emoji, if any. If we can't see the emoji, this might be missing most info.
    emoji_obj = (
        None  # The found emoji object, which will only exist if we can see the emoji
    )

    if ctx.args.isdigit():
        # We've been passed an emoji id, presumably
        emoji_obj = discord.utils.get(ctx.client.emojis, id=int(ctx.args))
        if not emoji_obj:
            # Okay, we can't see the emoji in our list.
            # We can't do much with just an id
            emoji = {"id": int(ctx.args)}
            if not enlarged_only or not await emoji_validity(emoji):
                await ctx.reply("No emojis with this id found!")
                return
        else:
            # We found the emoji, get the emoji dict
            emoji = await get_custom_emoji(ctx, emoji_obj.guild.id, emoji_obj.id)
    elif ctx.args.endswith(">") and ctx.args.startswith("<"):
        # We've probably been passed an actual emoji (don't count on it)
        # Extact what's hopefully an id from the string
        id_str = ctx.args[ctx.args.rfind(":") + 1 : -1]
        if not id_str.isdigit():
            # This is a.. what then?
            # Just quit and pretend this never happened
            await ctx.error_reply("No matching emojis found!")
        else:
            # Look for an emoji with this id
            emoji_obj = discord.utils.get(ctx.client.emojis, id=int(id_str))
            if not emoji_obj:
                # Okay, we can't see the emoji in our list.
                # We'll have to build the emoji manually with name and id.
                emoji = {
                    "name": ctx.args[
                        ctx.args.find(":") + 1 : ctx.args.rfind(":")
                    ].strip(),
                    "id": id_str,
                    "animated": ctx.args[1] == "a",
                }
                if not await emoji_validity(emoji):
                    await ctx.error_reply("No matching emojis found!")
                    return
            else:
                # We found the emoji, get the emoji dict
                emoji = await get_custom_emoji(ctx, emoji_obj.guild.id, emoji_obj.id)
    elif not all(ord(char) < 128 for char in ctx.args):
        # There's unicode in this string
        # TODO: handle unicode emojis
        # Consider using https://github.com/twitter/twemoji/blob/master/scripts/build.js#L571
        await ctx.error_reply("Sorry, I cannot handle built in emojis at this time!")
        return
    else:
        # Time to do a lookup
        # First, grab the emojis in the current guild and see if any of them match
        if not ctx.guild:
            emojis = None
        else:
            emojis = await get_custom_emojis(ctx, ctx.guild.id)

        if emojis:
            # Check exact matches
            index = next(
                (
                    i
                    for i, emoji in enumerate(emojis)
                    if em_str == emoji["name"].lower()
                ),
                None,
            )
            if index is None:
                # Check inexact matches
                index = next(
                    (
                        i
                        for i, emoji in enumerate(emojis)
                        if em_str in emoji["name"].lower()
                    ),
                    None,
                )

            if index is not None:
                emoji = emojis[index]
                emoji_obj = discord.utils.get(ctx.client.emojis, id=emoji["id"])

        if not emoji:
            # Okay, no matches found in the current guild, let's look at everyone else.
            # Exact matches
            emoji_obj = discord.utils.get(ctx.client.emojis, name=ctx.args)
            if not emoji:
                # Inexact matches
                emoji_obj = next(
                    filter(lambda e: (em_str in e.name.lower()), ctx.client.emojis),
                    None,
                )

            if emoji_obj:
                # Great, we found an emoji. Get the emoji dict.
                emoji = await get_custom_emoji(ctx, emoji_obj.guild.id, emoji_obj.id)
            else:
                # We coldn't find the emoji. Nothing we can do with a partial name
                await ctx.error_reply("No matching emojis found!")
                return

    # Just in case we somehow came out with no emoji
    if emoji is None:
        await ctx.error_reply("No matching emojis found!")
        return

    # At this point, we should have enough of the emoji to do what is requested.
    # Start handling the different output cases.
    if react_only:
        react_message = None
        if not ctx.guild or not ctx.ch.permissions_for(ctx.author).add_reactions:
            return await ctx.error_reply(
                "You do not have permissions to add reactions here!"
            )

        if ctx.guild:
            if not ctx.ch.permissions_for(ctx.guild.me).add_reactions:
                return await ctx.error_reply(
                    "I do not have permissions to add reactions here!"
                )

        # If a messageid to react to was specified, get it. Otherwise get the previous message in the channel.
        if flags["to"]:
            if not flags["to"].isdigit():
                return await ctx.error_reply("`to` argument must be a message id.")
            react_message = await ctx.ch.fetch_message(int(flags["to"]))
            if not react_message:
                # Couldn't find the requested message to react to
                await ctx.error_reply("Couldn't find that message in this channel!")
                return
        else:
            if flags["up"] and flags["up"].isdigit() and int(flags["up"]) < 20:
                distance = int(flags["up"]) + 1
            else:
                distance = 2
            # Grab logs
            # TODO: Does this need permission checking?
            logs = ctx.ch.history(limit=distance)
            async for message in logs:
                react_message = message

            # If there wasn't a previous message, whinge
            if react_message is None or react_message == ctx.msg:
                await ctx.reply("Couldn't find a message to react to!")
                return

        # React to the specified message.
        # Wrap this in try/except in case the message was deleted in the meantime somehow.
        try:
            await ctx.client.http.add_reaction(
                ctx.ch.id, react_message.id, "{}:{}".format(emoji["name"], emoji["id"])
            )
        except discord.NotFound:
            pass
        except discord.HTTPException:
            await ctx.error_reply("I don't have this emoji, so I can't react with it!")

        # If we need to delete the source message, do this now
        if ctx.alias == "sree":
            try:
                await ctx.msg.delete()
            except discord.Forbidden:
                pass

        # Monitor the react message for reactions for a bit. If someone else reacts, remove our reaction.
        try:
            reaction, _ = await ctx.client.wait_for(
                "reaction_add",
                check=lambda reaction, user: (
                    user != ctx.client.user
                    and reaction.message == react_message
                    and not isinstance(reaction.emoji, str)
                    and reaction.emoji.id == int(emoji["id"])
                ),
                timeout=60,
            )
        except asyncio.TimeoutError:
            pass

        # Remove our reaction (if possible)
        try:
            await react_message.remove_reaction(
                reaction.emoji, ctx.guild.me if ctx.guild else ctx.client.user
            )
        except Exception:
            pass
    elif enlarged_only:
        # We just want to post an embed with the enlarged emoji as the image.
        elink = read_emoji_link(emoji)
        embed = discord.Embed(colour=discord.Colour.light_grey())
        await ctx.reply(embed=embed.set_image(url=elink))
    elif info:
        # We want to post the embed with the enlarged emoji, and as much info as we can get.
        prop_list = []
        value_list = []

        if "name" in emoji:
            prop_list.append("Name")
            value_list.append(emoji["name"])
        if "id" in emoji:
            prop_list.append("ID")
            value_list.append("`{}`".format(emoji["id"]))
        prop_list.append("Image link")
        value_list.append("[Click here]({})".format(read_emoji_link(emoji)))
        if "user" in emoji:
            prop_list.append("Creator")
            value_list.append("{username}#{discriminator}".format(**emoji["user"]))
        if emoji_obj is not None:
            prop_list.append("Server")
            value_list.append(emoji_obj.guild.name if emoji_obj.guild else "Unknown")

            created_ago = strfdelta(datetime.datetime.now(datetime.UTC) - emoji_obj.created_at)
            created = emoji_obj.created_at.strftime("%I:%M %p, %d/%m/%Y")
            prop_list.append("Created at")
            value_list.append(created)
            prop_list.append("")
            value_list.append(created_ago)

        desc = prop_tabulate(prop_list, value_list)
        embed = discord.Embed(
            color=discord.Colour.light_grey(), description=desc, title="Emoji info!"
        )
        embed.set_image(url=read_emoji_link(emoji))
        await ctx.reply(embed=embed)
    else:
        # Final use case, just post the emoji
        await ctx.reply(
            "<{a}:{name}:{id}>".format(a="a" if emoji["animated"] else "", **emoji)
        )
