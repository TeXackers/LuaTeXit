import asyncio
import logging
import sys

from cmdClient.logger import cmd_log_handler
from discord import AllowedMentions
from paraArgs import args
from utils.lib import mail, split_text

# Setup the logger
logger = logging.getLogger()
log_fmt = logging.Formatter(
    fmt="[{levelname[0]}][{asctime}.{msecs:03.0f}]{message}",
    datefmt="%y-%m-%d %H:%M:%S",
    style="{",
)


class _DiscordContextFilter(logging.Filter):
    """
    Reformats records from discord.py's own loggers (e.g. 'discord.gateway')
    to match the '<context> | <message>' style used by our own `log()` calls.
    """

    def filter(self, record) -> bool:
        if record.name == "discord" or record.name.startswith("discord"):
            record.msg = f"[{'Discord':^18}] {record.getMessage().replace('\n', '\\n')}"
            record.args = None
        return True


discord_context_filter = _DiscordContextFilter()

term_handler = logging.StreamHandler(sys.stdout)
term_handler.setFormatter(log_fmt)
term_handler.addFilter(discord_context_filter)
logger.addHandler(term_handler)
logger.setLevel(logging.INFO)

_client = None


def _level_name(level):
    for name, value in logging.getLevelNamesMapping().items():
        if value == level:
            return name
    return str(level)


# Define the context log format and attach it to the command logger as well
@cmd_log_handler
def log(message, context="CLIENT", level=logging.INFO, post=True):
    # Use a single line logging format so the files are more parseable
    context_clean = str(context).capitalize()
    logger.log(level, f"[{context_clean:^18}] {message.replace('\n', '\\n')}")

    # Fire and forget to the channel logger, if it is set up
    if post and _client is not None:
        task = asyncio.ensure_future(live_log(message, context_clean, level))
        task.add_done_callback(lambda t: t.exception() or None)


# Live logger that posts to the logging channels
async def live_log(message, context, level):
    context_clean = str(context).capitalize()
    if level >= logging.INFO:
        log_chid = _client.conf.get("log_channel")

        # Generate the log messages
        header = f"[{_level_name(level)[:1]}][{context_clean}]"
        blocks = split_text(message, blocksize=1900, code=False) if len(message) > 1900 else [message]

        if len(blocks) > 1:
            blocks = [f"```\n{header}[{i + 1}/{len(blocks)}]\n{block}\n```" for i, block in enumerate(blocks)]
        else:
            blocks = [f"```\n{header}\n{blocks[0]}\n```"]

        # Post the log messages
        if log_chid:
            [await mail(_client, log_chid, content=block, allowed_mentions=AllowedMentions.none()) for block in blocks]

        if level >= logging.ERROR:
            error_chid = _client.conf.get("error_channel")
            if error_chid:
                [
                    await mail(_client, error_chid, content=block, allowed_mentions=AllowedMentions.none())
                    for block in blocks
                ]


def attach_log_client(client):
    """
    Attach the client to the logger so it can post to the log channels.
    """
    global _client
    _client = client
