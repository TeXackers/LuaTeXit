import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING, Any, NamedTuple, Protocol, TypeVar, cast

import discord
from discord import (
    Message,
)

if TYPE_CHECKING:
    from asyncio import Task

    # Need these for pyright/pylance to work
    from modules.Tex.core.tex_compile import (
        make_plain_luatex,
        make_plain_pdftex,
        makeluatex,
        makepythontex,
        maketex,
        makexetex,
    )
    from modules.Typst.core.typst_compile import maketypst
    from settings.ctx_guildsetting import get_guild_setting
    from utils.ctx_addons import (
        best_prefix,
        clean_arg_str,
        confirm_sent,
        dm_reply,
        embedreply,
        format_usage,
        live_reply,
        log,
        mail,
        offer_delete,
        run_in_shell,
        safe_delete_msgs,
        usage_embed,
    )
    from utils.interactive import (
        ask,
        listen_for,
        multi_selector,
        on_input,
        pager,
        pager_v2,
        pager_v2_pages,
        selector,
    )
    from utils.seekers import (
        find_channel,
        find_member,
        find_message,
        find_role,
    )

    from .cmdClient import cmdClient
    from .Command import Command

from .Layouts import DebugEmbedView, ErrorEmbedView


class _Registrable(Protocol):
    """only need name for lookups"""

    __name__: str


F = TypeVar("F", bound=_Registrable)


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
        "alias",
        "arg_str",
        "args",
        "author",
        "ch",
        "cleanup_on_edit",
        "client",
        "cmd",
        "guild",
        "msg",
        "objects",
        "prefix",
        "reparse_on_edit",
        "sent_messages",
        "server",
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
    def util(cls: type[Context], util_func: F) -> F:
        """
        Decorator to make a utility function available as a Context instance method
        """
        setattr(cls, util_func.__name__, util_func)
        return util_func

    if TYPE_CHECKING:
        # For function objects as class attributes (#27)
        embedreply = embedreply
        live_reply = live_reply
        log = log
        run_in_shell = run_in_shell
        best_prefix = best_prefix
        format_usage = format_usage
        confirm_sent = confirm_sent
        offer_delete = offer_delete
        mail = mail
        safe_delete_msgs = safe_delete_msgs
        dm_reply = dm_reply
        clean_arg_str = clean_arg_str
        usage_embed = usage_embed

        listen_for = listen_for
        selector = selector
        multi_selector = multi_selector
        pager_v2_pages = pager_v2_pages
        pager_v2 = pager_v2
        pager = pager
        on_input = on_input
        ask = ask

        find_role = find_role
        find_channel = find_channel
        find_member = find_member
        find_message = find_message

        maketex = maketex
        makeluatex = makeluatex
        makexetex = makexetex
        make_plain_luatex = make_plain_luatex
        make_plain_pdftex = make_plain_pdftex
        makepythontex = makepythontex
        maketypst = maketypst

        get_guild_setting = get_guild_setting

        # `reply`/`error_reply`/`traceback` are defined further down in this same file, so
        # they can't be imported the same way (pyright can't forward-reference a same-file
        # name from inside a class body) -- these three still need hand-written stubs, kept
        # deliberately close to their real implementations below to limit drift.
        async def reply(self, content: str | None = ..., **kwargs: Any) -> Message: ...
        async def error_reply(self, error_str: str) -> Message | None: ...
        async def traceback(self, helper_msg: str, error_str: str) -> Message | None: ...

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
    with suppress(discord.Forbidden, asyncio.TimeoutError):
        message: Message = await ctx.reply(
            view=ErrorEmbedView(error_str, discord.utils.format_dt(discord.utils.utcnow(), "F")),
        )
        ctx.sent_messages.append(message)
        return message


@Context.util
async def traceback(ctx: Context, helper_msg: str, error_str: str):
    """
    Notify the user of an error, and show traceback
    """
    with suppress(discord.Forbidden, asyncio.TimeoutError):
        out_msg: Message = await ctx.reply(
            view=DebugEmbedView(helper_msg, error_str, discord.utils.format_dt(discord.utils.utcnow(), style="F")),
        )
        ctx.sent_messages.append(out_msg)
        return out_msg
