import random

import discord
from cmdClient import Context  # noqa
from cmdClient.Format import emph
from cmdClient.Layouts import Body, Footer, Header, SectionWithThumbnail, TextEmbed
from constants import LuaTeXitCC
from discord.http import Route
from discord.ui import Container, LayoutView, Separator
from utils.lib import paginate_list, tabulate
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


async def get_user_avatar(ctx: Context, uid: int) -> str:
    """
    Fetches a user's global avatar URL, and return it if it exists.
    If the user does not have a global avatar, the default avatar will be returned.

    Parameters
    ----------
    uid: int
        The user's ID.

    Returns: str
        The direct URL to the user's global avatar.
    """

    res = await ctx.client.http.request(Route("GET", f"/users/{uid}"))
    if not res["avatar"]:
        return f"https://cdn.discordapp.com/embed/avatars/{int(res['discriminator']) % 5}.png"

    filetype: str = "webp" if res["avatar"].startswith("a_") else "png"

    return f"https://cdn.discordapp.com/avatars/{uid}/{res['avatar']}.{filetype}?size=1024"


async def get_server_avatar(ctx: Context, gid: int, uid: int) -> str | None:
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

    filetype: str = "gif" if res["avatar"].startswith("a_") else "png"

    return f"https://cdn.discordapp.com/guilds/{gid}/users/{uid}/avatars/{res['avatar']}.{filetype}?size=1024"


async def get_user_banner(ctx: Context, uid: int) -> str | None:
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

    return f"https://cdn.discordapp.com/banners/{uid}/{res['banner']}.{filetype}?size=2048"


@module.cmd(name="roleinfo", desc="Displays information about a role.", aliases=["role", "rinfo", "ri"])
@in_guild()
async def cmd_roleinfo(ctx: Context):
    """
    Usage``:
        {prefix}roleinfo [<role-name> | <role-mention> | <role-id>]
    Description:
        Provides information about the given role.
        If no role is provided, all of the roles in the guild will be listed.
    """
    # Get a sorted list of guild roles by position
    guild_roles: list[discord.Role] = sorted(ctx.guild.roles, key=lambda role: role.position)

    # Handle not having arguments, list all the current roles
    if not ctx.args:
        return await ctx.pager(paginate_list([role.name for role in reversed(guild_roles)], title="Guild roles"))

    role = await ctx.find_role(ctx.args, create=False, interactive=True)
    if not role:
        return None

    # Prepare the role properties
    role_colours: list[str] = [str(role.colour)]
    if role.secondary_colour:
        role_colours.append(str(role.secondary_colour))
    if role.tertiary_colour:
        role_colours.append(str(role.tertiary_colour))
    embed_colour: str = str(random.choice(role_colours))
    num_users: int = len(role.members)
    created: str = discord.utils.format_dt(role.created_at, style="f")
    created_ago: str = discord.utils.format_dt(role.created_at, style="R")
    hoisted: str = "Yes" if role.hoist else "No"
    mentionable: str = "Yes" if role.mentionable else "No"

    # Build the property/value table
    desc_fields: dict[str, str | int] = {
        "Unique ID": f"`{str(int(role.id))}`",
        "Colours": ", ".join(role_colours) if len(role_colours) > 1 else role_colours[0],
        "Hoisted": hoisted,
        "Can @?": mentionable,
        "Members": num_users,
        "Created": f"{created} ({created_ago})",
    }
    desc_text: str = tabulate(desc_fields)

    # Build the hierarchy graph
    pos = role.position
    position = ""
    for i in reversed(range(-7, 7)):
        line_pos = pos + i
        if line_pos < 0:
            break
        if line_pos >= len(guild_roles):
            continue
        position += "{}.   <@&{}> {}\n".format(
            len(guild_roles) - line_pos,
            guild_roles[line_pos].id,
            "👈️" if guild_roles[line_pos] == role else "🔰" if guild_roles[line_pos] == ctx.author.top_role else "",
        )

    desc_text += f"\n### Role hierarchy\n{position}\n-# 👈️: requested role; 🔰: your highest role"

    # Build the relative string
    diff_str = ""
    if ctx.guild.default_role != ctx.author.top_role:
        if role > ctx.author.top_role:
            diff_str = f"(This role is {emph('above')} your highest role)"
        elif role < ctx.author.top_role:
            diff_str = f"(This role is {emph('below')} your highest role.)"
        elif role == ctx.author.top_role:
            diff_str = f"(This is your {emph('highest')} role.)"
    else:
        diff_str = "(This is the default role for the guild.)"

    return await ctx.reply(
        view=TextEmbed(
            f"{role.name if len(role.name) < 26 else role.name[:25] + '...'}",
            desc_text,
            diff_str,
            discord.Colour.from_str(embed_colour),
        ),
    )


@module.cmd(name="rolemembers", desc="Lists members with a particular role.", aliases=["rolemems", "whohas"])
@in_guild()
async def cmd_rolemembers(ctx: Context) -> None:
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


@module.cmd(
    "userinfo",
    desc="Shows various information about a user.",
    aliases=["ui"],
    flags=["global"],
)
@in_guild()
async def cmd_userinfo(ctx: Context, flags: dict) -> None:
    """
    Usage``:
        {prefix}userinfo [user]
    Description:
        Sends information on the provided user.
        If no user is provided, the author will be used.
    """
    user: discord.Member = ctx.author

    if ctx.args:
        user = await ctx.find_member(ctx.args, interactive=True)
        if not user:
            return None
    # Consider Message references for selecting a user
    elif ctx.msg.reference:
        if ctx.msg.reference.resolved:
            user = await ctx.find_member(str(ctx.msg.reference.resolved.author.id))
            if not user:
                return None
    colour = user.colour if user.colour.value else LuaTeXitCC["yellow"]

    # prioritise guild banner/avatar
    if flags["global"]:
        banner = await get_user_banner(ctx, user.id)
        av = await get_server_avatar(ctx, ctx.guild.id, user.id)
    else:
        banner = user.guild_banner.url if user.guild_banner else await get_user_banner(ctx, user.id)
        av = user.guild_avatar.url if user.guild_avatar else await get_user_banner(ctx, user.id)

    numshared = sum(g.get_member(user.id) is not None for g in ctx.client.guilds)
    roles = [r.name for r in reversed(user.roles) if r.name != "@everyone"]

    desc_text: str = tabulate(
        {
            "Username": f"{str(user).split('#')[0]} {'🤖' if user.bot else '🫃'}",
            "Nickname": user.display_name,
            "User ID": f"`{str(user.id)}`",
            "Top role": (roles[0] if len(roles[0]) < 26 else f"{roles[0][:23]}...") if roles else "N/A",
            "Seen in": f"{numshared} guild{'s' if numshared > 1 else ''}",
            "Joined at": discord.utils.format_dt(user.joined_at, "R") if user.joined_at else "N/A",
            "Created at": discord.utils.format_dt(user.created_at, "R"),
        },
    )

    role_text = f"\n### Roles\n{('`' + '`, `'.join(roles) + '`') if roles else 'N/A'}"

    # if user.joined_at:  # joined_at is Optional
    #     assert ctx.guild is not None
    #     joined = sorted(
    #         (mem for mem in ctx.guild.members if mem.joined_at),
    #         key=lambda mem: mem.joined_at,
    #     )
    #     pos = joined.index(user)
    #     positions = []
    #     for i in range(-3, 4):
    #         line_pos = pos + i
    #         if line_pos < 0:
    #             continue
    #         if line_pos >= len(joined):
    #             break
    #         positions.append(
    #             "{:>4}.   {} {}".format(line_pos + 1, ">" if joined[line_pos] == user else " ", joined[line_pos])
    #         )
    #     join_seq = "```markdown\n{}\n```".format("\n".join(positions))

    container = Container(accent_colour=colour)
    if banner:
        container.add_item(
            discord.ui.MediaGallery(
                discord.MediaGalleryItem(banner, description=f"Banner for {user.display_name}"),
            ),
        )
    container.add_item(Header(f"{user}"))
    container.add_item(SectionWithThumbnail(desc_text, av or user.display_avatar.url))
    # add user's banner as Image if it exists

    container.add_item(Body(role_text))
    container.add_item(Footer(f"{discord.utils.format_dt(ctx.msg.created_at, 'f')} | Requested by: {ctx.author}"))

    v = LayoutView()
    v.add_item(container)
    return await ctx.reply(view=v)


@module.cmd("guildinfo", desc="Shows information about the guild.", aliases=["serverinfo", "gi", "si"])
@in_guild()
async def cmd_guildinfo(ctx: Context) -> None:
    """
    Usage``:
        {prefix}guildinfo
    Description:
        Shows information about the guild you are in.
    """

    total = len(ctx.server.channels)

    bots: int = sum(m.bot for m in ctx.server.members)
    humans: int = max((ctx.server.member_count or 0) - bots, 0)

    desc_text = tabulate(
        {
            "Owner": f"<@{ctx.server.owner_id}>",
            "Created": f"{discord.utils.format_dt(ctx.server.created_at, 'f')} ({discord.utils.format_dt(ctx.server.created_at, 'R')})",
            "Members": f"{humans} 🫃, {bots} 🤖 | {bots + humans} total",
            "Large?": "Yes" if ctx.server.large else "No",
            "Channels": f"{len(ctx.server.text_channels)} 📝, {len(ctx.server.voice_channels)} 🗣️ ({total} total)",
            "Premium": f"Level {ctx.server.premium_tier} | {ctx.server.premium_subscription_count} boost{'s' if ctx.server.premium_subscription_count != 1 else ''} total",
        },
    )

    container = Container(
        accent_colour=ctx.server.owner.colour if ctx.server.owner.colour.value else discord.Colour.teal(),
    )
    if ctx.server.banner:
        container.add_item(
            discord.ui.MediaGallery(
                discord.MediaGalleryItem(str(ctx.server.banner), description=f"Banner for {ctx.server.name}"),
            ),
        )
    container.add_item(Header(f"{ctx.server}"))
    container.add_item(SectionWithThumbnail(desc_text, str(ctx.server.icon)))
    container.add_item(Footer(f"{discord.utils.format_dt(ctx.msg.created_at, 'f')} | Requested by: {ctx.author}"))

    v = LayoutView()
    v.add_item(container)

    return await ctx.reply(view=v)


@module.cmd("channelinfo", desc="Displays information about a channel.", aliases=["ci"])
@in_guild()
async def cmd_channelinfo(ctx: Context) -> None:
    """
    Usage``:
        {prefix}channelinfo [<channel-name> | <channel-mention> | <channel-id>]
    Description:
        Gives information on a text channel, voice channel, or category.
        If no channel is provided, the current channel will be used.
    """
    tv = {
        "text": "Text 📝",
        "voice": "Voice 🗣️",
        "private": "Private 🔒",
        "group": "Group 👥",
        "category": "Category",
        "news": "Announcement 📣",
        "stage_voice": "Stage 🎙️",
        "news_thread": "Public thread",
        "private_thread": "Private thread",
        "public_thread": "Public thread",
        "forum": "Forum 🗂️",
        "media": "Media 🎬",
    }

    # Definitions to shorten the character count
    gch = ctx.server.channels
    me = ctx.server.me
    user = ctx.author
    # Disallow selecting channels that the user and bot cannot see.
    valid = [ch for ch in gch if (ch.permissions_for(user).read_messages) and (ch.permissions_for(me).read_messages)]
    ch = ctx.ch
    if ctx.args:
        ch = await ctx.find_channel(ctx.args, interactive=True, collection=valid)
        if not ch:
            return None

    desc_fields = {
        "Name": f"{ch.mention}" if not isinstance(ch, discord.CategoryChannel) else f"{ch.name}",
        "Unique ID": f"`{ch.id}`",
        "Channel Type": tv[str(ch.type)],
        "Category": f"{ch.category}" if ch.category else "None",
        "NSFW?": "Yes" if getattr(ch, "nsfw", False) else "No",
    }

    match type(ch):
        case discord.VoiceChannel | discord.StageChannel:
            desc_fields["User limit"] = f"{ch.user_limit}" if ch.user_limit else "Unlimited"
        case discord.Thread:
            desc_fields["Last active"] = (
                f"{discord.utils.format_dt(ch.last_message.created_at, 'R')}" if ch.last_message else "No messages"
            )
        case discord.CategoryChannel:
            desc_fields["# Channels"] = f"{len(ch.channels)}"

    desc_fields["Created"] = (
        f"{discord.utils.format_dt(ch.created_at, 'f')} ({discord.utils.format_dt(ch.created_at, 'R')})"
    )

    desc_text = tabulate(desc_fields)

    container = Container(accent_colour=LuaTeXitCC["purple"])
    container.add_item(Header(f"{ch}"))
    container.add_item(Separator())
    container.add_item(SectionWithThumbnail(desc_text, str(ch.guild.icon)))
    if isinstance(ch, discord.TextChannel) and ch.topic:
        container.add_item(Body(f"\n**Description**\n{ch.topic}"))
    container.add_item(Footer(f"{discord.utils.format_dt(ctx.msg.created_at, 'f')} | Requested by: {ctx.author}"))

    v = LayoutView()
    v.add_item(container)

    return await ctx.reply(view=v)


@module.cmd("avatar", desc="Obtains the mentioned user's avatar, or your own.", aliases=["av"], flags=["global"])
async def cmd_avatar(ctx: Context, flags) -> None:
    """
    Usage``:
        {prefix}avatar [<username> | <user ID> | <user mention> | <partial lookup>]
        [--global]
    Description:
        Displays the avatar of the provided user. If no user is provided, the author will be used.
        Hyperlinks the user's avatar so it can be viewed online.
    Flags::
        global: Display the user's global avatar, if set.
    """
    if not ctx.args:
        user = ctx.author
        colour = LuaTeXitCC["purple"]
    else:
        user = await ctx.find_member(ctx.args, interactive=True)
        if not user:
            ctx.error_reply("User not found.")
        colour = LuaTeXitCC["yellow"] if user.colour.value == "#000000" else user.colour

    if flags["global"]:
        avatar_url = await get_user_avatar(ctx, user.id)
        using = "global avatar"
    elif ctx.guild and user.guild_avatar:
        avatar_url = await get_server_avatar(ctx, ctx.guild.id, user.id)
        using = "server avatar"
    else:
        avatar_url = user.display_avatar.url
        using = "display avatar (in lieu)"

    avatar_url = (
        user.display_avatar.url
        if (flags["global"] and user.display_avatar)
        else user.guild_avatar.url
        if (ctx.guild and user.guild_avatar)
        else user.display_avatar.url
    )

    container = Container(accent_colour=colour)
    container.add_item(Body(f"**{user}**'s {using}"))
    container.add_item(
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(avatar_url, description=f"Avatar for {user.display_name}"),
        ),
    )
    container.add_item(Footer(f"Requested by: {ctx.author}"))

    v = LayoutView()
    v.add_item(container)
    return await ctx.reply(view=v)
