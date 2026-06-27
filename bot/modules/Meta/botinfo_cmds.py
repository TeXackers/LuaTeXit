import platform
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime

import discord
import psutil
from cmdClient import Context  # noqa
from utils.ctx_addons import best_prefix  # noqa
from utils.lib import prop_tabulate

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
async def cmd_curr_load(ctx: type[Context]) -> None:
    table_fields: list = []

    # separate for MacOS vs linux
    if platform.system() == "Darwin":
        # OS Name
        table_fields.append(("OS", platform.platform(terse=True).replace("-", " ")))

        # Architecture for MacOS
        table_fields.append(("Arch", platform.mac_ver()[2].upper()))

        # CPU Name
        table_fields.append(
            ("CPU", subprocess.check_output(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode())
        )
        # CPU
        table_fields.append(
            ("CPU Load", f"{psutil.cpu_count(logical=False)}C/{psutil.cpu_count()}T ({psutil.cpu_percent()}%)")
        )
    else:
        # OS Name
        table_fields.append(("OS", platform.platform(terse=True).replace("-", " ")))
        # Architecture for linux
        table_fields.append(("Arch", platform.machine()))
        # CPU Name
        table_fields.append(("CPU", "Intel Core i5-8350U"))

    # Memory
    mem_total: int = psutil.virtual_memory().total >> 20
    mem_used: int = psutil.virtual_memory().used >> 20
    table_fields.append(("Memory", f"{mem_used}/{mem_total} MiB ({mem_used / mem_total * 100:.1f}%)"))

    # Versions
    py_version: str = platform.python_version()
    py_build: str = platform.python_build()[1]
    compiler: str = platform.python_compiler()
    table_fields.append(("Py Version", f"{py_version} ({py_build})"))

    # luatex version
    table_fields.append(
        (
            "LuaTeX Version",
            subprocess.check_output(["luatex", "--version"])
            .decode()
            .split("\n")[0]
            .split(", ")[1]
            .replace("Version ", ""),
        )
    )
    # XeTeX parsed differently
    # Example output:
    # XeTeX 3.141592653-2.6-0.999996 (TeX Live 2024/Arch Linux)
    table_fields.append(
        ("XeTeX Version", subprocess.check_output(["xetex", "--version"]).decode().split("\n")[0].split(" ")[1])
    )
    # Typst version
    table_fields.append(
        ("Typst Version", subprocess.check_output(["typst", "--version"]).decode().split("\n")[0].split(" ")[1])
    )
    # Compiler version
    table_fields.append(("Compiler", compiler))

    # Tabulate
    fields, values = zip(*table_fields)
    table: str = prop_tabulate(fields, values)

    # Build embed
    desc = f"{table}"
    embed = discord.Embed(title="Top", color=discord.Colour.red(), description=desc)

    # Finally, send embed
    await ctx.reply(embed=embed)


@module.cmd("about", desc="Shard status and bot statistics.")
async def cmd_about(ctx: type[Context]):
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
        shard_str = f"{ctx.client.shard_id} of {ctx.client.shard_count}"
        table_fields.append(("Shard", shard_str))

        guild_str = f"{len(ctx.client.guilds)} (~{ctx.client.shard_count * len(ctx.client.guilds)} total)"
        table_fields.append(("Shard guilds", guild_str))

        member_str = f"{len(list(ctx.client.get_all_members()))} (~{ctx.client.shard_count * len(list(ctx.client.get_all_members()))} total)"
        table_fields.append(("Shard members", member_str))
    else:
        table_fields.append(("Guilds", len(ctx.client.guilds)))
        table_fields.append(("Members", len(list(ctx.client.get_all_members()))))

    # Commands
    table_fields.append(("Commands", f"{len(ctx.client.cmds)}, with {len(ctx.client.cmd_names)} command keywords"))

    # Memory
    mem = psutil.virtual_memory()
    mem_str = f"{mem.used / (1024**3):.1f} GiB used out of {mem.total / (1024**3):.1f} GiB ({mem.used / mem.total * 100:.1f}%)"
    table_fields.append(("Memory", mem_str))

    # CPU Usage
    table_fields.append(("CPU Usage", f"{psutil.cpu_percent()}%"))
    # Python version
    table_fields.append(("Python", f"{sys.version.split('\n')[0].split('(')[0]} (discord.py: {discord.__version__})"))

    # Platform
    table_fields.append(("Platform", platform.platform(terse=True)))

    # Tabulate
    fields, values = zip(*table_fields)
    table = prop_tabulate(fields, values)

    # Create info string for top of description
    info = ctx.client.app_info["info_str"].format(prefix=ctx.best_prefix())

    # Create link string for bottom of description
    links = "[Support server]({}), [Invite me]({}), [Contribute!]({})".format(
        ctx.client.app_info["support_guild"],
        ctx.client.app_info["invite_link"],
        # ctx.client.app_info["donate_link"],
        ctx.client.app_info["github"],
    )

    # Build embed
    desc = f"{info}\n{table}\n{links}"
    embed = discord.Embed(title="About Me", color=discord.Colour.red(), description=desc)

    # Finally, send embed
    await ctx.reply(embed=embed)


@module.cmd("ping", desc="Check heartbeat and API latency.", aliases=["pong"])
async def cmd_ping(ctx: type[Context]):
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
async def cmd_invite(ctx: type[Context]):
    """
    Usage``:
        {prefix}invite
    Description:
         Replies with a link to invite me to your server.
    """
    await ctx.reply(
        "Visit [here](https://discordapp.com/api/oauth2/authorize?client_id=871978350393065572&permissions=0&scope=bot) to invite me!"
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
