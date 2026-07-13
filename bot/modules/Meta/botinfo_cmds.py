import asyncio
import platform
import re
import subprocess
import sys
from typing import TYPE_CHECKING

from constants import LuaTeXitCC
from utils.cache import async_ttl_cache

if TYPE_CHECKING:
    import datetime

import datetime

import discord
import psutil
from cmdClient import Context  # noqa
from cmdClient.Layouts import GenericFullEmbed
from utils.lib import tabulate
from wards import get_team_info

from .module import meta_module as module

"""
Commands providing basic meta information about the bot.

Commands provided:
    about:
        Sends an embed with the status of the bot process,
        and statistics about the current shard client.
    ping:
        Test the API round trip response time through message edits.
    invite:
        Reply with an invite link for the current app.
    support:
        Reply with an invite link to the support guild for the current app.
"""


async def check_output(*args: str) -> bytes:
    """Run subprocess.check_output off the event loop thread."""
    return await asyncio.to_thread(subprocess.check_output, args)


# for caching tlmgr/luatex and so on
cached_check_output = async_ttl_cache(days=14)(check_output)


async def get_member_count(client: discord.Client) -> int:
    """Count members visible to the client."""
    return len(list(client.get_all_members()))


# member iteration is expensive on large bots, so cache it briefly
cached_member_count = async_ttl_cache(days=1)(get_member_count)


@module.cmd("about", desc="Shard status and bot statistics.")
async def cmd_about(ctx: Context):
    """
    Usage``:
        {prefix}about
    Description:
        Sends an embed with basic statistics about the current shard, host, and bot process.
    """
    status: dict = {}
    restrict_invite: bool = False

    # Current owner/admins/developers, from the bot's Discord team
    owner_id, _ = await get_team_info(ctx.client, "owner")
    _, admin_ids = await get_team_info(ctx.client, "admin")
    _, team_ids = await get_team_info(ctx.client, "team")
    dev_ids = team_ids - admin_ids

    status["Owner"] = str(ctx.client.get_user(owner_id) or owner_id)

    if admin_ids and admin_ids != {owner_id}:
        admin_field_name = "Admin" if len(admin_ids) == 1 else "Admins"
        status[admin_field_name] = ", ".join(str(ctx.client.get_user(uid) or uid) for uid in admin_ids)

    if dev_ids and dev_ids != {owner_id}:
        dev_field_name = "Developer" if len(dev_ids) == 1 else "Developers"
        status[dev_field_name] = ", ".join(str(ctx.client.get_user(uid) or uid) for uid in dev_ids)

    # Bot version using current git tag (or latest tag, if not currently on one)
    try:
        git_version = (
            (await cached_check_output("git", "describe", "--tags", "--always")).decode().strip().split("-")[0]
        )
    except subprocess.CalledProcessError:
        git_version = "unknown"
    status["Version"] = git_version

    # Shards, guilds, and members
    member_count = await cached_member_count(ctx.client)
    if member_count > 10000:
        restrict_invite = True

    if ctx.client.shard_count > 1:
        shard_str = f"{ctx.client.shard_id} of {ctx.client.shard_count}"
        status["Shard"] = shard_str

        guild_str = f"{len(ctx.client.guilds)} (~{int(ctx.client.shard_count) * len(ctx.client.guilds)} total)"
        status["Shard guilds"] = guild_str

        member_str = f"{member_count} (~{ctx.client.shard_count * member_count} total)"
        status["Shard members"] = member_str
    else:
        status["Guilds"] = len(ctx.client.guilds)
        status["Members"] = member_count

    # Commands, adjusted for any commands disabled in this guild
    disabled_here = ctx.client.objects["disabled_guild_commands"].get(ctx.guild.id, []) if ctx.guild else []
    status["Commands"] = f"{len(ctx.client.cmds) - len(disabled_here)}"

    # Hardware uptime using `uptime` shell command
    # Output looks like: 15:49:53  up 108 days,  8:12,  2 users,  load average: 0.50, 0.32, 0.30
    # (or "up  8:12,  2 users, ..." / "up 5 min,  1 user, ..." for shorter uptimes)
    uname = await check_output("uptime")
    up_section = re.search(r"up\s+(.*?),\s*\d+\s+users?,", uname.decode())
    uptime_str = up_section.group(1).strip() if up_section else ""

    days_match = re.search(r"(\d+)\s+day", uptime_str)
    days = int(days_match.group(1)) if days_match else 0

    hm_match = re.search(r"(\d+):(\d+)", uptime_str)
    hours = int(hm_match.group(1)) if hm_match else 0

    status["Uptime"] = f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"

    # CPU Usage
    status["CPU Usage"] = f"{psutil.cpu_percent()}%"

    # Memory
    mem_total: int = psutil.virtual_memory().total >> 20
    mem_used: int = psutil.virtual_memory().used >> 20
    status["Memory"] = f"{mem_used}/{mem_total} MiB ({mem_used / mem_total * 100:.1f}%)"

    # Python version
    status["Python"] = f"{sys.version.split('\n')[0].split('(')[0]} (discord.py: {discord.__version__})"

    # Platforms
    ## OS from /etc/os-release, fields NAME and VERSION_ID
    version_id: str = await cached_check_output("/bin/grep", "VERSION_ID", "/etc/os-release")
    version_id = version_id.decode().strip().split("=")[1].replace('"', "")
    status["OS"] = f"openSUSE Tumbleweed {version_id}"
    status["Kernel"] = platform.platform(aliased=True)

    # LaTeX and other things we use
    tlmgr_str = await cached_check_output("tlmgr", "--version")
    # example output:
    # tlmgr revision 79491 (2026-06-27 19:40:15 +0200)
    # tlmgr using installation: /usr/local/texlive/2026
    # TeX Live (https://tug.org/texlive) version 2026
    # we only need build number (79491) and date (2026-06-27)
    tlmgr_lines = tlmgr_str.decode().split("\n")
    tlmgr_build = tlmgr_lines[0].split(" ")[2]
    tlmgr_date = tlmgr_lines[0].split(" ")[3].replace("(", "").replace(")", "")
    status["TeXLive"] = (
        f"{tlmgr_build} (tlmgr: {discord.utils.format_dt(datetime.datetime.strptime(tlmgr_date, '%Y-%m-%d'), 'R')})"  # noqa
    )

    # LuaTeX version
    status["LuaTeX Version"] = (
        (await cached_check_output("luatex", "--version"))
        .decode()
        .split("\n")[0]
        .split(", ")[1]
        .replace("Version ", "")
    )

    # Typst
    status["Typst Version"] = (await cached_check_output("typst", "--version")).decode().split("\n")[0].split(" ")[1]
    # Tabulate
    fields_text: str = tabulate(status)

    # Create info string for top of description
    desc_text: str = ctx.client.app_info["info_str"].format(prefix=await ctx.best_prefix())

    # check if we have more than 10000 users using the bot, make a boolean

    # Create link string for bottom of description
    invite_text = f"[Invite me]({ctx.client.app_info['invite_link']}), " if not restrict_invite else ""
    links = f"[Support server]({ctx.client.app_info['support_guild']}), {invite_text}[Contribute!]({ctx.client.app_info['github']})"

    # Finally, send embed
    return await ctx.reply(
        view=GenericFullEmbed(
            header="About LuaTeXit",
            body=f"{desc_text}\n{fields_text}",
            footer=links,
            # use bot's avatar
            thumbnail_url=ctx.client.user.display_avatar.url,
            accent_colour=LuaTeXitCC["yellow"],
        ),
    )


@module.cmd("ping", desc="Check heartbeat and API latency.", aliases=["pong"])
async def cmd_ping(ctx: Context):
    """
    Usage``:
        {prefix}ping
    Description:
        Test the API round trip response by editing a message.
        Also sends the websocket protocol latency (heartbeat).
    """
    # Edit a message and see how long it takes
    msg = await ctx.reply("Beep")
    maketime: datetime.datetime = discord.utils.utcnow()
    await msg.edit(content="Boop")
    edittime: datetime.datetime = discord.utils.utcnow()
    latency = (edittime - maketime).microseconds // 1000

    await msg.edit(content=f"Ping: `{latency}`ms.\nHeartbeat: `{ctx.client.latency * 1000:.0f}`ms.")


@module.cmd("invite", desc="Sends the bot's invite link", aliases=["inv"])
async def cmd_invite(ctx: Context):
    """
    Usage``:
        {prefix}invite
    Description:
         Replies with a link to invite me to your server.
    """
    member_count = await cached_member_count(ctx.client)
    if member_count >= 10000:
        return await ctx.error_reply(
            "I'm currently used by too many members to accept new server invites "
            "without Discord's message content verification. Please check back later!",
        )

    return await ctx.reply(
        "Visit [here](https://discordapp.com/api/oauth2/authorize?client_id=871978350393065572&permissions=0&scope=bot) to invite me!",
    )


@module.cmd("support", desc="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage``:
        {prefix}support
    Description:
        Sends the invite link to my support guild.
    """
    await ctx.reply("Join my support server: {}".format(ctx.client.app_info["support_guild"]))
