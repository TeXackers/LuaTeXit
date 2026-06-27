import datetime

import discord
from cmdClient import Context  # noqa
from constants import LuaTeXitCC
from discord import Status
from discord.http import Route
from utils.lib import emb_add_fields, format_activity, join_list, paginate_list, prop_tabulate, strfdelta
from wards import in_guild

from .module import info_module as module

# Provides serverinfo, userinfo, roleinfo, whohas, avatar
"""
Provides a number of information lookup commands on Discord objects

Commands provided:
    userinfo:
        Provides info on the provided user
    avatar:
        Displays the avatar for the provided user
    role:
        Displays info on the provided role, or displays a list of roles
    rolemembers:
        Displays the members of a role
    serverinfo:
        Displays info on the current server
    channelinfo:
        Displays information about a specified channel
"""


async def get_server_avatar(ctx, gid, uid):
    """
    Fetches a member's server avatar URL, and return it if it exists.
    If the member does not have a server avatar, None will be returned.

    Parameters
    ----------
    gid: int
        The guild ID.
    uid: int
        The member's user ID.

    Returns: str
        The direct URL to the member's server avatar.

    """

    res = await ctx.client.http.request(Route("GET", f"/guilds/{gid}/members/{uid}"))
    if not res["avatar"]:
        return None

    filetype = "gif" if res["avatar"].startswith("a_") else "png"

    url = "https://cdn.discordapp.com/guilds/{}/users/{}/avatars/{}.{}?size=1024".format(
        gid, uid, res["avatar"], filetype
    )

    return await url


async def get_user_banner(ctx, uid):
    """
    Fetches a user's profile banner, and return it if it exists.
    If the member does not have a profile banner, None will be returned.

    Parameters
    ----------
    uid: int
        The user's ID.

    Returns: str
        The direct URL to the user's profile banner.

    """

    res = await ctx.client.http.request(Route("GET", f"/users/{uid}"))
    if not res["banner"]:
        return None

    filetype = "gif" if res["banner"].startswith("a_") else "png"

    url = "https://cdn.discordapp.com/banners/{}/{}.{}?size=2048".format(uid, res["banner"], filetype)
    return await url


@module.cmd(name="roleinfo", desc="Displays information about a role.", aliases=["role", "rinfo", "ri"])
@in_guild()
async def cmd_roleinfo(ctx: type[Context]):
    """
    Usage``:
        {prefix}roleinfo [<role-name> | <role-mention> | <role-id>]
    Description:
        Provides information about the given role.
        If no role is provided, all of the roles in the guild will be listed.
    """
    # Get a sorted list of guild roles by position
    guild_roles = sorted(ctx.guild.roles, key=lambda role: role.position)

    # Handle not having arguments, list all the current roles
    if not ctx.args:
        await ctx.pager(paginate_list([role.name for role in reversed(guild_roles)], title="Guild roles"))
        return
    role = await ctx.find_role(ctx.args, create=False, interactive=True)
    if not role:
        return

    # Prepare the role properties
    colour = role.colour if role.colour.value else discord.Colour.light_grey()
    num_users = len(role.members)
    created = role.created_at.strftime("%I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(
        strfdelta(
            datetime.datetime.now(tz=datetime.timezone.utc) - role.created_at.replace(tzinfo=datetime.timezone.utc),
            minutes=True,
        )
    )
    hoisted = "Yes" if role.hoist else "No"
    mentionable = "Yes" if role.mentionable else "No"

    # Build the property/value table
    prop_list = ["Colour", "Hoisted", "Mentionable", "Number of members", "Created at", ""]
    value_list = [str(role.colour), hoisted, mentionable, num_users, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    # Build the hierarchy graph
    pos = role.position
    position = "```markdown\n"
    for i in reversed(range(-3, 4)):
        line_pos = pos + i
        if line_pos < 0:
            break
        if line_pos >= len(guild_roles):
            continue
        position += "{:>4}.   {} {}\n".format(
            len(guild_roles) - line_pos, ">" if guild_roles[line_pos] == role else " ", guild_roles[line_pos]
        )

    # Build the relative string
    position += "```"
    if ctx.guild.default_role != ctx.author.top_role:
        if role > ctx.author.top_role:
            diff_str = "(This role is above your highest role.)"
        elif role < ctx.author.top_role:
            diff_str = "(This role is below your highest role.)"
        elif role == ctx.author.top_role:
            diff_str = "(This is your highest role!)"
        position += diff_str

    # Finally, build the embed and reply
    title = f"{role.name} ({role.id})"
    embed = discord.Embed(title=title, colour=colour, description=desc)
    emb_fields = [("Position in the hierarchy", position, 0)]
    emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@module.cmd(name="rolemembers", desc="Lists members with a particular role.", aliases=["rolemems", "whohas"])
@in_guild()
async def cmd_rolemembers(ctx: type[Context]) -> None:
    """
    Usage``:
        {prefix}rolemembers [<role-name> | <role-mention> | <role-id> | <partial lookup>]
    Description:
        Lists all of the users in the specified role.
    """
    if not ctx.args:
        return await ctx.error_reply("Please provide a role to list the members of.")

    role = await ctx.find_role(ctx.args, create=False, interactive=True)
    if not role:
        return None

    members = role.members
    if len(members) == 0:
        await ctx.reply("No members have this role.")
        return None
    return await ctx.pager(paginate_list(members, title=f"Members in {role.name}"))


@module.cmd("userinfo", desc="Shows various information about a user.", aliases=["uinfo", "ui", "user", "profile"])
@in_guild()
async def cmd_userinfo(ctx: type[Context]) -> None:
    """
    Usage``:
        {prefix}userinfo [user]
    Description:
        Sends information on the provided user.
        If no user is provided, the author will be used.
    """
    user = ctx.author
    if ctx.args:
        user = await ctx.find_member(ctx.args, interactive=True)
        if not user:
            return
    # Consider Message references for selecting a user
    elif ctx.msg.reference:
        if ctx.msg.reference.resolved:
            user = await ctx.find_member(str(ctx.msg.reference.resolved.author.id))
            if not user:
                return
    colour = user.colour if user.colour.value else LuaTeXitCC["yellow"]

    name = "{} {}".format(user, ctx.client.conf.emojis.getemoji("bot") if user.bot else "")

    banner = await get_user_banner(ctx, user.id)
    serverav = await get_server_avatar(ctx, ctx.guild.id, user.id)

    statusnames = {
        Status.offline: "Offline",
        Status.dnd: "Do Not Disturb",
        Status.online: "Online",
        Status.idle: "Away",
    }

    # Acceptable statuses to be considered as active.
    activestatus = [Status.online, Status.idle, Status.dnd]

    devicestatus = {
        "desktop": user.desktop_status in activestatus,
        "mobile": user.mobile_status in activestatus,
        "web": user.web_status in activestatus,
    }

    if any(devicestatus.values()):
        # String if the user is "online" on one or more devices.
        device = f"Active on {join_list(string=[k for k, v in devicestatus.items() if v], nfs=True)}"
    else:
        # String if the user isn't "online" on any device.
        device = "Not active on any device"

    activity = format_activity(user)
    presence = f"{ctx.client.conf.emojis.getemoji(user.status.name)} {statusnames[user.status]}"
    numshared = sum(g.get_member(user.id) is not None for g in ctx.client.guilds)
    shared = "{} guild{}".format(numshared, "s" if numshared > 1 else "")
    joined_ago = ctx.ts(user.joined_at)
    created_ago = ctx.ts(user.created_at)
    prop_list = ["Full name", "Nickname", "Presence", "Activity", "Device", "Seen in", "Joined at", "Created at"]
    value_list = [name, user.display_name, presence, activity, device, shared, joined_ago, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    roles = [r.name for r in reversed(user.roles) if r.name != "@everyone"]
    roles = ("`" + "`, `".join(roles) + "`") if roles else "None"

    embed = discord.Embed(color=colour, description=desc)
    embed.set_author(name=f"{user} ({user.id})", icon_url=user.avatar)
    if serverav:
        embed.set_thumbnail(url=serverav)
    else:
        embed.set_thumbnail(url=user.avatar)

    embed.add_field(name="Roles", value=roles, inline=False)

    if banner:
        embed.set_image(url=banner)

    if user.joined_at:  # joined_at is Optional
        joined = sorted((mem for mem in ctx.guild.members if mem.joined_at), key=lambda mem: mem.joined_at)
        pos = joined.index(user)
        positions = []
        for i in range(-3, 4):
            line_pos = pos + i
            if line_pos < 0:
                continue
            if line_pos >= len(joined):
                break
            positions.append(
                "{:>4}.   {} {}".format(line_pos + 1, ">" if joined[line_pos] == user else " ", joined[line_pos])
            )
        join_seq = "```markdown\n{}\n```".format("\n".join(positions))
        embed.add_field(name="Join order", value=join_seq, inline=False)

    await ctx.reply(embed=embed)


@module.cmd(
    "guildinfo", desc="Shows information about the guild.", aliases=["serverinfo", "sinfo", "si", "gi"], flags=["icon"]
)
@in_guild()
async def cmd_guildinfo(ctx: type[Context], flags: dict) -> None:
    """
    Usage``:
        {prefix}guildinfo [--icon]
    Description:
        Shows information about the guild you are in.
    Flags::
        icon: Sends the guild icon in an embed.
    """
    guild = ctx.guild

    if flags["icon"]:
        if not ctx.guild.icon:
            return await ctx.reply("The current guild has no custom icon set.")
        embed = discord.Embed(color=discord.Colour.light_grey())
        embed.set_image(url=guild.icon)
        return await ctx.reply(embed=embed)

    verif_descs = {
        "none": "Unrestricted",
        "low": "Must have a verified email",
        "medium": "Must be registered for more than 5 minutes",
        "high": "Must be a member for more than 10 minutes",
        "extreme": "Must have a verified phone number",
    }

    verif_level = guild.verification_level.name
    ver = f"{verif_level.title()} | {verif_descs[verif_level]}"

    text = len(guild.text_channels)
    voice = len(guild.voice_channels)
    category = len(guild.categories)
    total = len(guild.channels)

    statuses = [s for s in Status if s != Status.invisible]
    activestatus = [s for s in statuses if s != Status.offline]
    emoji = {s: ctx.client.conf.emojis.getemoji(s.name) for s in statuses}

    counts = dict.fromkeys(statuses, 0)
    desktop = mobile = web = 0

    for m in guild.members:
        counts[m.status] += 1

        desktop += m.desktop_status in activestatus
        mobile += m.mobile_status in activestatus
        web += m.web_status in activestatus

    status = "\n".join(f"{emoji[s]} - **{counts[s]}**" for s in statuses)
    devicestatus = f"🖥️ - **{desktop}**\n📱 - **{mobile}**\n🌎 - **{web}**"

    bots = sum(m.bot for m in guild.members)
    humans = guild.member_count - bots
    members = "{} human{}, {} bot{} | {} total".format(
        humans, "s" if humans > 1 else "", bots, "s" if bots > 1 else "", guild.member_count
    )

    owner = f"{guild.owner} ({guild.owner.id})"
    icon = f"[Icon Link]({guild.icon})" if guild.icon else "No guild icon set"
    mfa = "Enabled" if guild.mfa_level else "Disabled"
    channels = "{} text, {} voice, {} category {} | {} total".format(
        text, voice, category, "ies" if category > 1 else "y", total
    )
    boosts = "Level {} | {} boost{} total".format(
        guild.premium_tier, guild.premium_subscription_count, "" if guild.premium_subscription_count == 1 else "s"
    )
    created = guild.created_at.strftime("%I:%M %p, %d/%m/%Y")
    created_ago = ctx.ts(guild.created_at)

    prop_list = [
        "Owner",
        "Icon",
        "Verification",
        "2FA",
        "Roles",
        "Members",
        "Channels",
        "Server Boosts",
        "Created at",
        "",
    ]
    value_list = [owner, icon, ver, mfa, len(guild.roles), members, channels, boosts, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=guild.owner.colour if guild.owner.colour.value else discord.Colour.teal(), description=desc
    )
    embed.set_author(name=f"{ctx.guild} ({ctx.guild.id})")
    embed.set_thumbnail(url=guild.icon)

    emb_fields = [("Member Status", status, 0), ("Member Status by Device", devicestatus, 0)]

    emb_add_fields(embed, emb_fields)
    return await ctx.reply(embed=embed)


@module.cmd("channelinfo", desc="Displays information about a channel.", aliases=["ci"], flags=["topic"])
@in_guild()
async def cmd_channelinfo(ctx: type[Context], flags: dict) -> None:
    """
    Usage``:
        {prefix}channelinfo [<channel-name> | <channel-mention> | <channel-id] [--topic]
    Description:
        Gives information on a text channel, voice channel, or category.
        If no channel is provided, the current channel will be used.
    Flags::
        topic: Reply with only the channel topic.
    """
    tv = {
        "text": "Text channel",
        "voice": "Voice channel",
        "category": "Category",
        "news": "Announcement channel",
        "store": "Store channel",
        "public_thread": "Public thread",
        "private_thread": "Private thread",
        "news_thread": "Public thread",
        "stage_voice": "Stage channel",
    }

    # Definitions to shorten the character count
    gch = ctx.guild.channels
    me = ctx.guild.me
    user = ctx.author
    # Disallow selecting channels that the user and bot cannot see.
    valid = [ch for ch in gch if (ch.permissions_for(user).read_messages) and (ch.permissions_for(me).read_messages)]
    ch = ctx.ch
    if ctx.args:
        ch = await ctx.find_channel(ctx.args, interactive=True, collection=valid)
        if not ch:
            return None

    if flags["topic"]:
        if isinstance(ch, discord.TextChannel):
            return await ctx.reply(
                f"**Channel topic for {ch.mention}**:\n{ch.topic}"
                if ch.topic
                else f"{ch.mention} doesn't have a topic.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        return await ctx.reply("Only text channels have topics!")

    # Generic embed info, valid for every channel type.
    name = f"{ch.name} [{ch.mention}]" if not isinstance(ch, discord.CategoryChannel) else f"{ch.name}"
    created = ch.created_at.strftime("%d/%m/%Y")
    created_ago = ctx.ts(ch.created_at)

    category = f"{ch.category} ({ch.category.id})" if ch.category else "None"

    embed = discord.Embed(color=LuaTeXitCC["yellow"])
    embed.set_author(name=f"Channel information for {ch.name}.")

    if isinstance(ch, discord.TextChannel):
        # Embed info specific to text channels.
        topic = ch.topic or "No topic."
        nsfw = "Yes" if ch.nsfw else "No"
        prop_list = ["Name", "Type", "ID", "NSFW", "Category", "Created at", ""]
        value_list = [name, tv[str(ch.type)], ch.id, nsfw, category, created, created_ago]

        if len(topic) > 30:
            embed.add_field(name="Topic", value=topic)
        else:
            prop_list.append("Topic")
            value_list.append(topic)
    elif isinstance(ch, (discord.VoiceChannel, discord.StageChannel)):
        # Embed info specific to voice channels.
        userlimit = ch.user_limit or "Unlimited"

        prop_list = ["Name", "Type", "ID", "Category", "Created at", "", "User limit"]
        value_list = [name, tv[str(ch.type)], ch.id, category, created, created_ago, userlimit]

        # List current members.
        if ch.members:
            mems = "\n".join(f"{mem} ({mem.id})" for mem in ch.members)
            members = f"```{mems}```"
            field = [(f"Members: {len(ch.members)}", members, 0)]
            emb_add_fields(embed, field)
        else:
            embed.add_field(name="Members", value="None")

    elif isinstance(ch, discord.ThreadChannel):
        # Embed info specific to threads.
        owner = ctx.guild.get_member(ch.owner_id)
        origin = f"{ctx.guild.get_channel(ch.parent_id)} [<#{ch.parent_id}>]"
        dur = int(ch.auto_archive_duration / 60)
        auto_archive = "In {} hour{}".format(dur, "s" if dur > 1 else "")
        last_modified = ctx.ts(ch.archive_timestamp)

        prop_list = ["Name", "Origin", "Type", "ID", "Owner", "Auto archive", "Last Modified"]
        value_list = [name, origin, tv[str(ch.type)], ch.id, owner, auto_archive, last_modified]

    else:
        # If any other type is present, provide generic information only.
        prop_list = ["Name", "Type", "ID", "Created at", ""]
        value_list = [name, tv[str(ch.type)], ch.id, created, created_ago]

    if isinstance(ch, discord.CategoryChannel):
        # List visible channels in a category
        valid = [chan for chan in ch.channels if chan.permissions_for(ctx.author).read_messages]
        if valid:
            chlist = ", ".join(chan.mention if isinstance(chan, discord.TextChannel) else chan.name for chan in valid)
            field = [(f"Channels under this category: {len(ch.channels)}", chlist, 0)]
            emb_add_fields(embed, field)

    # Add the embed description
    desc = prop_tabulate(prop_list, value_list)
    embed.description = desc

    return await ctx.reply(embed=embed)


@module.cmd("avatar", desc="Obtains the mentioned user's avatar, or your own.", aliases=["av"], flags=["server"])
async def cmd_avatar(ctx: type[Context], flags) -> None:
    """
    Usage``:
        {prefix}avatar [<username> | <user ID> | <user mention> | <partial lookup>]
        [--server]
    Description:
        Displays the avatar of the provided user. If no user is provided, the author will be used.
        Hyperlinks the user's avatar so it can be viewed online.
    Flags::
        server: Display the user's server avatar, if set.
    """

    user = ctx.author
    if ctx.guild:
        if ctx.args:
            user = await ctx.find_member(ctx.args, interactive=True)
            if not user:
                return None
        colour = LuaTeXitCC["yellow"] if user.colour.value == "#000000" else user.colour
    else:
        colour = LuaTeXitCC["purple"]

    if flags["server"]:
        if not ctx.guild:
            return await ctx.error_reply("This flag can only be used in a server.")

        avatar_url = await get_server_avatar(ctx, ctx.guild.id, user.id)
        if not avatar_url:
            return await ctx.error_reply(f"{user} has no server avatar set.")

    else:
        avatar_url = user.avatar

    desc = f"Click [here]({avatar_url}) to view the {'GIF' if user.is_avatar_animated() else 'image'}."
    embed = discord.Embed(colour=colour, description=desc)
    embed.set_author(name=f"{user}'s Avatar")
    embed.set_image(url=avatar_url)

    return await ctx.reply(embed=embed)
