import asyncio  # noqa
import datetime
from collections import namedtuple

import discord

# from .logger import log
from . import (
    cmdClient,  # noqa
    lib,
)
from .Command import Command  # noqa
from .Layouts import ErrorEmbedView  # noqa

FlatContext = namedtuple(
    "FlatContext",
    (
        "msg",
        "ch",
        "guild",
        "server",
        "arg_str",
        "cmd",
        "alias",
        "author",
        "prefix",
        "cleanup_on_edit",
        "reparse_on_edit",
        "sent_messages",
    ),
)


class Context(object):
    __slots__ = (
        "client",
        "msg",
        "ch",
        "guild",
        "server",
        "objects",
        "args",
        "arg_str",
        "cmd",
        "alias",
        "author",
        "prefix",
        "sent_messages",
        "cleanup_on_edit",
        "reparse_on_edit",
        "tasks",
    )

    def __init__(self, client, **kwargs):
        self.client = client  # type: cmdClient.cmdClient

        self.msg: discord.Message = kwargs.pop("message", None)

        self.ch: discord.abc.Messageable | None = (
            self.msg.channel if self.msg is not None else kwargs.pop("channel", None)
        )
        self.guild: discord.Guild | None = (
            self.msg.guild if self.msg is not None else kwargs.pop("guild", None)
        )
        self.server: discord.Guild | None = self.guild
        self.author: discord.User | discord.Member = (
            self.msg.author if self.msg is not None else kwargs.pop("author", None)
        )

        self.arg_str = kwargs.pop("arg_str", None)  # type: str
        self.cmd: discord.ext.commands.Command | None = kwargs.pop("cmd", None)
        self.alias = kwargs.pop("alias", None)  # type: str
        self.prefix: str | None = kwargs.pop("prefix", None)

        self.cleanup_on_edit = kwargs.pop(
            "cleanup_on_edit", self.cmd.handle_edits if self.cmd is not None else True
        )

        self.reparse_on_edit = kwargs.pop(
            "reparse_on_edit", self.cmd.handle_edits if self.cmd is not None else True
        )

        # Argument string, intended to be overriden by argument parsers
        self.args = self.arg_str  # type:str

        # Cache of messages sent in this context.
        self.sent_messages = []  # type: List[discord.Message]

        # Context tasks, including for the final wrapped command
        self.tasks = []  # type: List[asyncio.Task]

    @classmethod
    def util(cls, util_func):
        """
        Decorator to make a utility function available as a Context instance method
        """
        setattr(cls, util_func.__name__, util_func)

    def flatten(self):
        """
        Returns a flat version of the current context for debugging or caching.
        Does not store `objects`.
        Intended to be overriden if different cache data is needed.
        """
        return FlatContext(
            msg=self.msg.id if self.msg else None,
            ch=self.ch.id if self.ch else None,
            guild=self.guild.id if self.guild else None,
            server=self.guild.id if self.guild else None,
            arg_str=self.arg_str,
            cmd=self.cmd.name if self.cmd else None,
            alias=self.alias,
            author=self.author.id if self.author else None,
            prefix=self.prefix,
            cleanup_on_edit=self.cleanup_on_edit,
            reparse_on_edit=self.reparse_on_edit,
            sent_messages=tuple([message.id for message in self.sent_messages]),
        )


@Context.util
async def reply(ctx, content=None, reference: discord.MessageReference | None = None, allowed_mentions = discord.AllowedMentions.none(), **kwargs) -> discord.Message:
    """
    Helper function to reply in the current channel.
    """

    message: discord.Message = await ctx.ch.send(
        content=content,
        reference=reference, 
        allowed_mentions=allowed_mentions,
        **kwargs
    )
    ctx.sent_messages.append(message)
    return message


@Context.util
async def error_reply(ctx, error_str):
    """
    Notify the user of a user level error.
    Typically, this will occur in a red embed, posted in the command channel.
    """
    # embed = discord.Embed(
    #     colour=discord.Colour.red(),
    #     description=error_str,
    #     timestamp=datetime.datetime.now(datetime.UTC),
    # )
    try:
        # message: discord.Message = await ctx.ch.send(embed=embed)
        message = await ctx.reply(view=ErrorEmbedView(error_str, ctx.ts(datetime.datetime.now(datetime.UTC))))
        ctx.sent_messages.append(message)
        return message
    except discord.Forbidden:
        message = await ctx.reply(view=ErrorEmbedView(error_str, ctx.ts(datetime.datetime.now(datetime.UTC))))
        ctx.sent_messages.append(message)
        return message
