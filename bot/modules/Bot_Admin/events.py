import discord
from cmdClient import cmdClient
from utils.lib import mail

from .module import bot_admin_module as module

"""
Event handlers for posting the leave/join guild messages in the guild log

Handlers:
    log_left_guild:
        Posts to the guild log when the bot leaves a guild
    log_joined_guild:
        Posts to the guild log when the bot joins a guild
"""


async def log_left_guild(client: cmdClient, guild: discord.Guild):
    # Build embed
    embed = discord.Embed(
        title=f"`{guild.name} (ID: {guild.id})`",
        colour=discord.Colour.red(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="Left guild!")
    embed.set_thumbnail(url=guild.icon)

    # Add more specific information about the guild
    embed.add_field(name="Owner", value=f"{guild.owner.name} (ID: {guild.owner.id})", inline=False)
    embed.add_field(name="Members (cached)", value=f"{len(guild.members)}", inline=False)
    embed.add_field(name="Now chatting in", value=f"{len(client.guilds)} guilds", inline=False)

    # Retrieve the guild log channel and log the event
    log_chid = client.conf.get("guild_log_ch")
    if log_chid:
        await mail(client, log_chid, embed=embed)


async def log_joined_guild(client: cmdClient, guild: discord.Guild):
    owner = guild.owner
    icon = guild.icon

    bots = 0
    known = 0
    unknown = 0
    other_members: set[int] = {mem.id for mem in client.get_all_members() if mem.guild != guild}

    for member in guild.members:
        if member.bot:
            bots += 1
        elif member.id in other_members:
            known += 1
        else:
            unknown += 1

    mem1 = "people I know" if known != 1 else "person I know"
    mem2 = "new friends" if unknown != 1 else "new friend"
    mem3 = "bots" if bots != 1 else "bot"
    mem4 = "total members"
    known = f"`{known}`"
    unknown = f"`{unknown}`"
    bots = f"`{bots}`"
    total = f"`{guild.member_count}`"
    mem_str = f"{known:<5}\t{mem1},\n{unknown:<5}\t{mem2},\n{bots:<5}\t{mem3}, and\n{total:<5}\t{mem4}."
    created = guild.created_at.strftime("%I:%M %p, %d/%m/%Y")

    embed = discord.Embed(
        title=f"`{guild.name} (ID: {guild.id})`",
        colour=discord.Colour.green(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="Joined guild!")
    embed.set_thumbnail(url=icon)

    embed.add_field(name="Owner", value=f"{owner} (ID: {owner.id})", inline=False)
    embed.add_field(name="Created at", value=f"{created}", inline=False)
    embed.add_field(name="Members", value=mem_str, inline=False)
    embed.add_field(name="Now chatting in", value=f"{len(client.guilds)} guilds", inline=False)

    # Retrieve the guild log channel and log the event
    log_chid = client.conf.get("guild_log_ch")
    if log_chid:
        await mail(client, log_chid, embed=embed)


@module.init_task
def attach_guild_events(client):
    client.add_after_event("guild_join", log_joined_guild)
    client.add_after_event("guild_remove", log_left_guild)
