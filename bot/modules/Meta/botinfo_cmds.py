import sys
import platform
import psutil
import subprocess
import re
# from datetime import datetime

import discord
from cmdClient import Context

from utils.lib import prop_tabulate
from utils.ctx_addons import best_prefix  # noqa

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

@module.cmd("stat", desc="Hardware Stats and Load.")
async def cmd_curr_load(ctx: Context) -> None:
    table_fields: list = []

    # Dev for LuaTeXit
    table_fields.append(("Developer", r"Leothelion#3743"))

    # OS Name
    table_fields.append(("OS", platform.platform(terse=True).replace("-", " ")))

    # Architecture for MacOS
    table_fields.append(("Arch", platform.mac_ver()[2].upper()))

    # CPU Name
    table_fields.append(("CPU", subprocess.check_output(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip().decode()))
    # CPU
    table_fields.append(("CPU Load", f"{psutil.cpu_count(logical=False)}C/{psutil.cpu_count()}T ({psutil.cpu_percent()}%)"))

    # Memory
    mem_total: int = psutil.virtual_memory().total >> 20
    mem_used: int = psutil.virtual_memory().used >> 20
    table_fields.append(("Memory", f"{mem_used}/{mem_total} MiB ({mem_used / mem_total * 100:.1f}%)"))

    # Versions
    py_version, py_build = sys.version.split("\n")
    compiler: str = re.findall(r"\((.*)\)", py_build)[0]
    table_fields.append(("Py Version", py_version.split("(")[0]))

    table_fields.append(("Lua Version", subprocess.check_output(['lua', '-v']).decode().split("  ")[0].replace("Lua ", "")))
    table_fields.append(("LuaTeX Version",
                         subprocess.check_output(["luatex", "--version"]).decode().split("\n")[0]\
                         .split(", ")[1].replace("Version ", "")))
    table_fields.append(("XeTeX Version",
                         subprocess.check_output(["xetex", "--version"]).decode().split("\n")[0]\
                         .split(", ")[1].replace("Version ", "")))
    table_fields.append(("Compiler", compiler))


    # Tabulate
    fields, values = zip(*table_fields)
    table: str = prop_tabulate(fields, values)

    # Build embed
    desc = f"{table}"
    embed = discord.Embed(title="Top", color=discord.Colour.red(), description=desc)

    # Finally, send embed
    await ctx.reply(embed=embed)

@module.cmd("about",
            desc="Shard status and bot statistics.")
async def cmd_about(ctx: Context):
    """
    Usage``:
        {prefix}about
    Description:
        Sends an embed with basic statistics about the current shard, host, and bot process.
    """
    table_fields = []

    # Current developers
    current_devs = ctx.client.app_info["dev_list"]
    dev_str = ", ".join(str(ctx.client.get_user(devid) or devid) for devid in current_devs)
    table_fields.append(("Developers", dev_str))

    # Shards, guilds, and members
    if ctx.client.shard_count > 1:
        shard_str = "{} of {}".format(ctx.client.shard_id, ctx.client.shard_count)
        table_fields.append(("Shard", shard_str))

        guild_str = "{} (~{} total)".format(
            len(ctx.client.guilds),
            ctx.client.shard_count * len(ctx.client.guilds)
        )
        table_fields.append(("Shard guilds", guild_str))

        member_str = "{} (~{} total)".format(
            len(list(ctx.client.get_all_members())),
            ctx.client.shard_count * len(list(ctx.client.get_all_members()))
        )
        table_fields.append(("Shard members", member_str))
    else:
        table_fields.append(("Guilds", len(ctx.client.guilds)))
        table_fields.append(("Members", len(list(ctx.client.get_all_members()))))

    # Commands
    table_fields.append((
        "Commands",
        "{}, with {} command keywords".format(len(ctx.client.cmds), len(ctx.client.cmd_names))
    ))

    # Memory
    mem = psutil.virtual_memory()
    mem_str = "{0:.2f}GB used out of {1:.2f}GB ({mem.percent}%)".format(
        mem.used/(1024 ** 3), mem.total/(1024 ** 3), mem=mem
    )
    table_fields.append(("Memory", mem_str))

    # CPU Usage
    table_fields.append((
        "CPU Usage",
        "{}%".format(psutil.cpu_percent())
    ))

    # API version
    table_fields.append((
        "API version",
        "{} ({})".format(discord.__version__, discord.version_info[3])
    ))

    # Python version
    table_fields.append(("Py version", sys.version.split("\n")[0]))

    # Platform
    table_fields.append(("Platform", platform.platform()))

    # Tabulate
    fields, values = zip(*table_fields)
    table = prop_tabulate(fields, values)

    # Create info string for top of description
    info = ctx.client.app_info["info_str"].format(prefix=ctx.best_prefix())

    # Create link string for bottom of description
    links = ("[Support Server]({}), [Invite Me]({}), [Help keep me running!]({})".format(
        ctx.client.app_info["support_guild"],
        ctx.client.app_info["invite_link"],
        ctx.client.app_info["donate_link"]
    ))

    # Build embed
    desc = "{}\n{}\n{}".format(info, table, links)
    embed = discord.Embed(title="About Me", color=discord.Colour.red(), description=desc)

    # Finally, send embed
    await ctx.reply(embed=embed)


@module.cmd("ping",
            desc="Check heartbeat and API latency.",
            aliases=["pong"])
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
    await msg.edit(content="Boop")
    latency = ((msg.edited_at - msg.created_at).microseconds) // 1000

    await msg.edit(content="Ping: `{}`ms.\nHeartbeat: `{:.0f}`ms.".format(latency, ctx.client.latency * 1000))


@module.cmd("invite",
            desc="Sends the bot's invite link",
            aliases=["inv"])
async def cmd_invite(ctx: Context):
    """
    Usage``:
        {prefix}invite
    Description:
         Replies with a link to invite me to your server.
    """
    await ctx.reply("Visit <{}> to invite me!".format(ctx.client.app_info["invite_link"]))


@module.cmd("support",
            desc="Sends the link to the bot guild")
async def cmd_support(ctx):
    """
    Usage``:
        {prefix}support
    Description:
        Sends the invite link to my support guild.
    """
    await ctx.reply("Join my support server: {}".format(ctx.client.app_info["support_guild"]))
