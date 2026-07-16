import inspect

import aiohttp
import anyio
import discord
import github
from anyio import Path as AsyncPath
from cmdClient import Context  # noqa
from github import Auth, Github
from wards import is_admin, is_dev, is_owner

from modules.Github.GithubColours import GithubColour

from .module import bot_admin_module as module

"""
Administration level commands for the bot
All commands require manager or master level permissions.

Commands provided:
    shutdown:
        Shuts down the bot, that's all
    setinfo:
        Sets the bot status, game/avatar/playing message
    dm:
        Sends a dm to the user with user id given
    logs:
        Attempts to send the logfile or last n lines of the log.
    showcmd:
        View the source of the specified command.
    issue:
        Files a new issue on the LuaTeXit GitHub repository.
"""

LUATEXIT_REPO = "texackers/LuaTeXit"

status_dict = {
    "online": discord.Status.online,
    "offline": discord.Status.offline,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}


activity_dict = {
    "playing": discord.ActivityType.playing,
    "streaming": discord.ActivityType.streaming,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
}


def _format_size(num_bytes: float) -> str:
    """Format a byte count using the largest unit that keeps it human-readable."""
    for unit in ("B", "KB", "MB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} GB"


@module.cmd("shutdown", desc="Shut down the client.", aliases=["restart"])
@is_admin()
async def cmd_shutdown(ctx: Context):
    """
    Usage``:
        {prefix}shutdown
    Description:
        Closes the client and shuts down the bot.

        *Requires you to be an owner of the bot.*
    """
    await ctx.reply("Shutting down...")
    await ctx.client.close()


@module.cmd(
    "setinfo",
    desc="Set my game, avatar, and status",
    aliases=["status", "setgame", "setstatus"],
    flags=["type=", "desc==", "url==", "avatar==", "status="],
)
@is_admin()
async def cmd_setgame(ctx: Context, flags):
    """
    Usage``:
        {prefix}setinfo [--type activity type] [--desc activity] [--url url] [--status status] [--avatar avatar_url]
    Description:
        Sets the current bot status and activity.

        *Requires you to be an owner of the bot.*
    Flags::
        type: Type of activity (see Activity Types section below).
        desc: Name of activity to show (shown after `playing`, `listening` etc).
        url: Streaming url if applicable.
        status: Client status (see Status section below).
        avatar: URL of the new avatar. Make sure you have a copy of the old one!
    Activity Types:
        One of `playing`, `streaming`, `listening` or `watching`.
    Status:
        One of `online`, `offline`, `idle` or `dnd`.
    """
    # Set the avatar if required
    if flags["avatar"]:
        avatar_url = flags["avatar"]
        async with aiohttp.get(avatar_url) as r:
            response = await r.read()
        await ctx.client.user.edit(avatar=response)

    # Build the activity
    activity = None
    if flags["desc"] or flags["type"]:
        activity = discord.Activity(
            type=activity_dict[flags["type"]] if flags["type"] else discord.ActivityType.playing,
            name=flags["desc"] or None,
            url=flags["url"] or None,
        )

    # Change the presence
    if flags["status"] or activity:
        await ctx.client.change_presence(status=flags["status"] or None, activity=activity)

    # Inform the user
    await ctx.reply("Updated!")


@module.cmd("dm", desc="Sends a direct message to a user, if possible.")
@is_owner()
async def cmd_dm(ctx: Context):
    """
    Usage``:
        {prefix}dm user_id message
    Description:
        Sends the specified message to the given `user_id` if possible.
    """
    # Parse the arguments
    splits = ctx.args.split(maxsplit=1)
    if len(splits) < 2 or not splits[0].isdigit():
        return await ctx.error_reply(ctx.format_usage())

    userid, message = splits

    # Find the user
    user: discord.User | None = ctx.client.get_user(int(userid))
    if user is None:
        try:
            user = await ctx.client.fetch_user(int(userid))
        except discord.NotFound:
            return await ctx.error_reply("This user does not exist!")

    # We can't send messages to ourself
    if user == ctx.client.user:
        return await ctx.error_reply("I cannot send a message to myself!")

    # Send the message
    try:
        await user.send(message)
    except discord.Forbidden:
        await ctx.error_reply(
            "I couldn't send the message. Maybe we don't share any servers with this user or they have us blocked?",
        )
    else:
        await ctx.reply("Message sent!")


@module.cmd("logs", desc="Read and return the bot logs.")
@is_owner()
async def cmd_logs(ctx: Context):
    """
    Usage``:
        {prefix}logs [lines]
    Description:
        Sends the logfile or the last `<lines>` lines of the log.
    """
    # Get the path to the log file from config
    logpath = AsyncPath(ctx.client.conf.get("LOGFILE"))

    if not ctx.args:
        # Check the logfile isn't too large to upload before attempting to send it
        limit = ctx.guild.filesize_limit if ctx.guild else discord.utils.DEFAULT_FILE_SIZE_LIMIT_BYTES
        size = (await logpath.stat()).st_size
        if size > limit:
            size_diff = size - limit
            return await ctx.error_reply(
                f"The log file is too large to send "
                f"(`{_format_size(size_diff)}` over the `{_format_size(limit)}` limit). Please download it manually."
            )

        return await ctx.reply(file=discord.File(logpath))

    # Retrieve the number of lines to send
    if not ctx.args.isdigit():
        return await ctx.error_reply(ctx.format_usage())
    lines = int(ctx.args)

    # Read the last <lines> lines of the log
    async with await anyio.open_file(logpath) as f:
        content = await f.read()
    logs = "\n".join(content.splitlines()[-lines:])

    # Strip all backticks
    logs_clean = logs.replace("```", "").replace("``", "")

    # Split the log blocks and page the result
    return await ctx.pager_v2(logs_clean, title=f"Last {lines} lines of the log", code=True, syntax="ini")


@module.cmd("showcmd", desc="Shows the source of a command.")
@is_dev()
async def cmd_showcmd(ctx: Context) -> None:
    """
    Usage:
        {prefix}showcmd <name>
    Description:
        Replies with the source for the specified command.
    """
    if not ctx.arg_str:
        return await ctx.error_reply("Please provide a command name.")

    # Get the command from the user arguments
    command = ctx.client.cmd_names.get(ctx.arg_str, None)
    if not command:
        return await ctx.error_reply("No command found.")

    cmd_func = command.func
    source = inspect.getsource(cmd_func)
    source = source.replace("```", "[codeblock]")

    return await ctx.pager_v2(source, title=f"Showing source for {ctx.arg_str}", code=True, syntax="python")


@module.cmd("issue", desc="File an issue on the LuaTeXit GitHub repository.", flags=["body=="])
@is_owner()
async def cmd_issue(ctx: Context, flags):
    """
    Usage``:
        {prefix}issue <title> --body <body>
    Description:
        Opens a new issue on `texackers/LuaTeXit` on GitHub, after a confirmation prompt.

        *Requires you to be an owner of the bot.*
    Flags::
        body: The body/description of the issue. If omitted, you will be prompted for it.
    """
    title = ctx.args.strip()
    if not title:
        return await ctx.error_reply(
            "Please provide a title for the issue. "
            "For example, `issue Broken font search --body The search times out on long queries.`",
        )

    body = flags["body"]
    if not body:
        body = await ctx.on_input("What should the body of the issue be? (`c` to cancel)", timeout=240)
        if body.lower() == "c":
            return await ctx.error_reply("Cancelled issue creation.")
        if not body.strip():
            return await ctx.error_reply("The issue body cannot be empty.")

    # Build a preview and confirm with the user before touching GitHub
    embed = discord.Embed(
        title=title,
        description=body,
        colour=GithubColour.github_green,
    )
    embed.set_author(name=f"{ctx.author} ({ctx.author.id})", icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text=f"This will be filed against {LUATEXIT_REPO}")

    preview = await ctx.reply(embed=embed)
    confirmed = await ctx.ask(f"Are you sure you want to open this issue on `{LUATEXIT_REPO}`?", use_msg=preview)
    await preview.edit(content="")
    if not confirmed:
        return await ctx.error_reply("Cancelled issue creation.")

    GITHUB_TOKEN: str = ctx.client.conf["GITHUB_AUTH_TOKEN"]
    github_api = Github(auth=Auth.Token(GITHUB_TOKEN), lazy=True)
    repo = github_api.get_repo(LUATEXIT_REPO)

    try:
        issue = repo.create_issue(title=title, body=body)
    except github.GithubException as e:
        match e.status:
            case 403:
                (reason := "I don't have permission to create issues on this repository [403].")
            case 404:
                (reason := f"`{LUATEXIT_REPO}` could not be found [404].")
            case 410:
                (reason := "issue creation has been disabled for this repository [410].")
            case 422:
                (reason := "validation failed -- check the title/body aren't empty [422].")
            case _:
                (reason := f"an undocumented (by GitHub) error occurred [Unknown Status Code: {e.status}].")
        return await ctx.error_reply(f"Could not create the issue, because {reason}")

    return await ctx.reply(f"Issue created: {issue.html_url}")
