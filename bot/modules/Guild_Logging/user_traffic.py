import asyncio
import logging

import discord
from cmdClient import Check
from discord import Status
from registry import Column, ColumnType, tableInterface, tableSchema
from settings import Channel, ColumnData, GuildSetting
from utils.lib import format_activity, join_list, prop_tabulate, strfdelta
from wards import guild_manager

from .module import guild_logging_module as module

# Map providing human readable names for each status
statusnames = {Status.offline: "Offline", Status.dnd: "Do Not Disturb", Status.online: "Online", Status.idle: "Away"}

# Statuses which are considered as active
activestatus = [Status.online, Status.idle, Status.dnd]


# Member join log event handler
async def join_logger(client, member):
    # Get the joinlog, return if it doesn't exist
    joinlog = client.guild_config.join_log.get(client, member.guild.id).value
    if not joinlog:
        return

    # Re-fetch the member to get better presence information
    await asyncio.sleep(1)
    member = member.guild.get_member(member.id)
    if member is None:
        return

    # Extract the required user information
    colour = member.colour if member.colour.value else discord.Colour.green()
    name = "{} {} ({})".format(member, client.conf.emojis.getemoji("bot") if member.bot else "", member.mention)
    activity = format_activity(member)
    presence = f"{client.conf.emojis.getemoji(member.status.name)} {statusnames[member.status]}"
    created_ago = f"({strfdelta(discord.utils.utcnow() - member.created_at, minutes=True)} ago)"
    created = member.created_at.strftime("%I:%M %p, %d/%m/%Y")

    devicestatus = {
        "desktop": member.desktop_status in activestatus,
        "mobile": member.mobile_status in activestatus,
        "web": member.web_status in activestatus,
    }
    if any(devicestatus.values()):
        # String if the member is "online" on one or more devices.
        device = f"Active on **{join_list(string=[k for k, v in devicestatus.items() if v], nfs=True)}**"
    else:
        # String if the user isn't "online" on any device.
        device = "Not active on any device"

    member_count = f"{len([m for m in member.guild.members if not m.bot])} Users, {len([m for m in member.guild.members if m.bot])} Bots | {member.guild.member_count} total"

    # Build the log embed
    prop_list = ["User", "Presence", "Activity", "Device", "Created at", "", "Member Count"]
    value_list = [name, presence, activity, device, created, created_ago, member_count]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=colour,
        title=f"{member} ({member.id})",
        description=desc,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="New {usertype} joined!".format(usertype="bot" if member.bot else "user"), url=member.avatar)
    embed.set_thumbnail(url=member.avatar)

    try:
        await joinlog.send(embed=embed)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    except Exception as e:
        client.log(
            f"Failed to post joinlog for member '{member}' (uid:{member.id}) in guild '{member.guild.name} (gid:{member.guild.id}). Exception: {e.__repr__()}",
            context="POST_JOINLOG",
            level=logging.WARNING,
        )


# member departure log event handler
async def departure_logger(client, member):
    # Get the departure log, return if it doesn't exist
    departure_log = client.guild_config.departure_log.get(client, member.guild.id).value
    if not departure_log:
        return

    # Extract member information
    name = f"{member.display_name} ({member.mention})"
    colour = discord.Colour.red()
    avatar = member.avatar

    joined_ago = f"({strfdelta(discord.utils.utcnow() - member.joined_at, minutes=True)} ago)"
    joined = member.joined_at.strftime("%I:%M %p, %d/%m/%Y")

    roles = [r.mention for r in member.roles if not r.is_default()]
    roles.reverse()
    rolestr = ", ".join(roles) if len(roles) > 0 else "None"

    member_count = f"{len([m for m in member.guild.members if not m.bot])} Users, {len([m for m in member.guild.members if m.bot])} Bots | {member.guild.member_count} total"

    prop_list = ["Member", "Joined at", "", "Roles", "Member count"]
    value_list = [name, joined, joined_ago, rolestr, member_count]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=colour,
        title=f"{member} ({member.id})",
        description=desc,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="{usertype} left!".format(usertype="Bot" if member.bot else "User"), url=avatar)
    embed.set_thumbnail(url=avatar)

    try:
        await departure_log.send(embed=embed)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    except Exception as e:
        client.log(
            f"Failed to post departure log for member '{member}' (uid:{member.id}) in guild '{member.guild.name} (gid:{member.guild.id}). Exception: {e.__repr__()}",
            context="POST_DEPARTURELOG",
            level=logging.WARNING,
        )


# Attach event handlers
@module.init_task
def attach_traffic_handlers(client):
    client.add_after_event("member_join", join_logger)
    client.add_after_event("member_remove", departure_logger)


# Define configuration settings
@module.guild_setting
class guild_joinlog(ColumnData, Channel, GuildSetting):
    attr_name = "join_log"
    category = "Logging"
    read_check: Check | None = None
    write_check: Check = guild_manager

    name = "joinlog"
    desc = "Channel to log information about new members."

    long_desc = "Channel where information about new members is posted."

    _table_interface_name = "guild_logging_joins"
    _data_column = "channelid"
    _delete_on_none = True


@module.guild_setting
class guild_departurelog(ColumnData, Channel, GuildSetting):
    attr_name = "departure_log"
    category = "Logging"
    read_check: Check | None = None
    write_check: Check = guild_manager

    name = "departurelog"
    desc = "Channel to log information about departing members."

    long_desc = "Channel where information about departing members is posted."

    _table_interface_name = "guild_logging_departures"
    _data_column = "channelid"
    _delete_on_none = True


# Define data schemas
member_traffic_schema = tableSchema(
    "member_traffic",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("userid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("first_joined", ColumnType.INT),  # Timestamp of first join seen or inferred
    Column("last_joined", ColumnType.INT),  # Timestamp of join at last departure
    Column("last_departure", ColumnType.INT),  # Timestamp of last departure
    Column("departure_name", ColumnType.SHORTSTRING),  # Name of user at last departure
    Column("departure_nickname", ColumnType.SHORTSTRING),  # Nickname of user at last departure
)

join_log_schema = tableSchema(
    "guild_logging_joins",
    Column("app", ColumnType.SHORTSTRING, primary=True, required=True),
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("channelid", ColumnType.SNOWFLAKE, required=True),
)

departure_log_schema = tableSchema(
    "guild_logging_departures",
    Column("app", ColumnType.SHORTSTRING, primary=True, required=True),
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("channelid", ColumnType.SNOWFLAKE, required=True),
)


# Attach data interfaces
@module.data_init_task
def attach_traffic_data(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, member_traffic_schema, shared=True),
        "member_traffic",
    )

    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, join_log_schema, shared=False),
        "guild_logging_joins",
    )

    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, departure_log_schema, shared=False),
        "guild_logging_departures",
    )
