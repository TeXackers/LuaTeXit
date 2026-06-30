from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, NamedTuple, cast

import discord
from discord import (
    Message,
)

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Awaitable, Callable

    from .cmdClient import cmdClient
    from .Command import Command

from .Layouts import DebugEmbedView, ErrorEmbedView


class FlatContext(NamedTuple):
    """A flat version of the Context object, for caching or debugging.

    Args:
        message_id (int | None): The ID of the message that triggered the command.
        channel_id (int | None): The ID of the channel where the command was triggered.
        guild_id (int | None): The ID of the guild where the command was triggered.
        server_id (int | None): The ID of the server where the command was triggered.
        arg_str (str | None): The argument string passed to the command.
        cmd (str | None): The name of the command that was triggered.
        alias (str | None): The alias used to trigger the command, if any.
        prefix (str | None): The prefix used to trigger the command, if any.
        cleanup_on_edit (bool): Whether to clean up messages on edit.
        reparse_on_edit (bool): Whether to reparse messages on edit.
        sent_messages (tuple[int, ...]): A tuple of IDs of messages sent in this context.
    """

    msg: int | None
    ch: int | None
    guild: int | None
    server: int | None
    arg_str: str | None
    cmd: str | None
    alias: str | None
    prefix: str | None
    cleanup_on_edit: bool
    reparse_on_edit: bool
    sent_messages: tuple[int, ...]


class Context:
    """Metadata (context) relevant to a command.

    Parameters
    ----------
    client: cmdClient
        The command client instance.
    message: Message | None
        Message from which a command was triggered.
    ch:
    """

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
        self.client: cmdClient = client

        self.msg: Message = kwargs.pop("message", None)
        self.ch: discord.abc.MessageableChannel = (
            self.msg.channel if self.msg is not None else kwargs.pop("channel", None)
        )
        self.guild: discord.Guild | None = self.msg.guild if self.msg is not None else kwargs.pop("guild", None)
        self.server: discord.Guild | None = self.guild
        self.author: discord.User | discord.Member = (
            self.msg.author if self.msg is not None else kwargs.pop("author", None)
        )

        self.arg_str: str = kwargs.pop("arg_str", None)
        self.cmd: Command = kwargs.pop("cmd", None)
        self.alias: str = kwargs.pop("alias", None)
        self.prefix: str = kwargs.pop("prefix", None)

        self.cleanup_on_edit: bool = kwargs.pop(
            "cleanup_on_edit",
            self.cmd.handle_edits if self.cmd is not None else True,
        )

        self.reparse_on_edit: bool = kwargs.pop(
            "reparse_on_edit",
            self.cmd.handle_edits if self.cmd is not None else True,
        )

        self.args: str = self.arg_str or ""

        self.sent_messages: list[Message] = []

        # Context tasks, including for the final wrapped command
        self.tasks: list[Task] = []

    @classmethod
    def util(cls: type[Context], util_func: Callable[..., Awaitable]) -> None:
        """
        Decorator to make a utility function available as a Context instance method
        """
        setattr(cls, util_func.__name__, util_func)

    def __getattr__(self, name: str) -> Any:
        """
        Allow dynamic utility methods registered with Context.util to type-check cleanly.
        """
        raise AttributeError(name)

    def flatten(self) -> FlatContext:
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
            prefix=self.prefix,
            cleanup_on_edit=self.cleanup_on_edit,
            reparse_on_edit=self.reparse_on_edit,
            sent_messages=tuple([message.id for message in self.sent_messages]),
        )


@Context.util
async def reply(
    ctx: Context,
    content: str | None = None,
    **kwargs,
) -> Message:
    """
    Helper function to reply in the current channel.
    """
    send_kwargs: dict[str, Any] = {"content": content, **kwargs}

    message: Message = await cast("discord.abc.Messageable", ctx.ch).send(**send_kwargs)
    ctx.sent_messages.append(message)
    return message


@Context.util
async def error_reply(ctx: Context, error_str: str):
    """
    Notify the user of a user level error.
    Typically, this will occur in a red embed, posted in the command channel.
    """
    with suppress(discord.Forbidden):
        message: Message = await ctx.reply(
            view=ErrorEmbedView(error_str, discord.utils.format_dt(discord.utils.utcnow(), "F")),
        )
        ctx.sent_messages.append(message)
        return message
    # try:
    #     message: Message = await ctx.reply(
    #         view=ErrorEmbedView(error_str, discord.utils.format_dt(discord.utils.utcnow(), "R"))
    #     )
    #     ctx.sent_messages.append(message)
    #     return message
    # except discord.Forbidden:
    #     message: Message = await ctx.reply(
    #         view=ErrorEmbedView(error_str, discord.utils.format_dt(discord.utils.utcnow(), "R"))
    #     )
    #     ctx.sent_messages.append(message)
    #     return message


@Context.util
async def traceback(ctx: Context, helper_msg: str, error_str: str):
    """
    Notify the user of an error, and show traceback
    """
    with suppress(discord.Forbidden):
        out_msg: Message = await ctx.reply(
            view=DebugEmbedView(helper_msg, error_str, discord.utils.format_dt(discord.utils.utcnow(), style="F")),
        )
        ctx.sent_messages.append(out_msg)
        return out_msg
    # try:
    #     out_msg: Message = await ctx.reply(
    #         view=DebugEmbedView(helper_msg, error_str, discord.utils.format_dt(discord.utils.utcnow(), style="F"))
    #     )
    #     ctx.sent_messages.append(out_msg)
    #     return out_msg
    # except discord.Forbidden:
    #     out_msg: Message = await ctx.reply(
    #         view=DebugEmbedView(helper_msg, error_str, discord.utils.format_dt(discord.utils.utcnow(), style="F"))
    #     )
    #     ctx.sent_messages.append(out_msg)
    #     return out_msg
