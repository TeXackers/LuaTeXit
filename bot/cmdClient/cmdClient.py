import asyncio
import importlib.machinery
import importlib.util
import itertools
import logging
import sys
import traceback
import types
from bisect import bisect
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .Module import Module

import discord
from cachetools import LRUCache
from discord import Message

from .Command import Command  # noqa
from .Context import Context, FlatContext
from .logger import current_mid, log
from .Module import Module

LUATEXIT_ID = 871978350393065572


class cmdClient(discord.Client):
    prefix: str | None

    baseModule: ClassVar[type[Module]] = Module
    default_module: ClassVar[Module | None]
    # List of loaded modules
    modules: ClassVar[list[Module]] = []
    # Command name cache, including aliases
    cmd_names: ClassVar[dict[str, Command]] = {}

    def __init__(
        self,
        prefix: str | None = None,
        owners: list[int] | None = None,
        ctx_cache: LRUCache | None = None,
        baseContext: type[Context] = Context,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.prefix = prefix
        self.owners = owners or []
        self.objects = {}
        self.app_info: dict = {}
        self.baseContext: type[Context] = Context
        self.ctx_cache: LRUCache = ctx_cache or LRUCache(1000)
        self.active_contexts: dict[int, Context] = {}
        self.extra_message_parsers = []
        self.background_tasks: set = set()

    @property
    def cmds(self) -> list[Command]:
        """
        A list of current available commands.
        """
        return list(itertools.chain(*[module.cmds for module in self.modules if module.enabled]))

    @classmethod
    def get_default_module(cls) -> Module:
        """
        Returns the default module, instantiating it if it does not exist.
        """
        if cls.default_module is None:
            cls.default_module = cls.baseModule()
        return cls.default_module

    @classmethod
    def cmd(cls, *args, mod: Module | None = None, **kwargs) -> Callable[[Callable], Command]:
        """
        Helper decorator to create a command with an optional module.
        If no module is specified, uses the class default module.
        """
        module: Module = mod or cls.get_default_module()
        return module.cmd(*args, **kwargs)

    @classmethod
    def update_cmdnames(cls) -> None:
        """
        Updates the command name cache.
        """
        cmds: dict[str, Command] = {}
        for module in cls.modules:
            if module.enabled:
                for cmd in module.cmds:
                    cmds[cmd.name] = cmd
                    for alias in cmd.aliases:
                        cmds[alias] = cmd
        cls.cmd_names = cmds

    async def valid_prefixes(self, message: Message) -> tuple[str, ...]:
        if self.prefix:
            return (self.prefix,)
        log("No prefix set and no prefix function implemented.", level=logging.ERROR)
        await self.close()
        return ()

    def set_valid_prefixes(self, func: Callable) -> None:
        self.valid_prefixes = func.__get__(self)

    def initialise_modules(self) -> None:
        log("Client module init")
        for module in self.modules:
            if module.enabled:
                module.initialise(self)

    async def launch_modules(self) -> None:
        log("Client module start")
        for module in self.modules:
            if module.enabled:
                await module.launch(self)

    async def on_ready(self) -> None:
        """
        Client has logged into discord and completed initialisation.
        Log a ready message with some basic statistics and info.
        """
        await self.launch_modules()

        ready_str = (
            f"{self.user} ({self.user.id or 'Unknown ID'}) launching in {len(self.guilds)} guilds\n"
            f"Default prefix: {self.prefix}\n"
            f"Commands: {len(self.cmds)}\n"
            f"GOTOV"
        )
        log(ready_str)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """
        An exception was caught in one of the event handlers.
        Log the exception with a traceback, and continue on.
        """
        log(f"Ignoring exception in {event_method}\n{traceback.format_exc()}", level=logging.ERROR)

    async def on_message(self, message: Message) -> None:
        """
        Event handler for `message`.
        Intended to be overridden.
        """
        await self.parse_message(message)

    async def on_message_edit(self, before: Message, after: Message) -> None:
        if before.content != after.content:
            if after.id in self.ctx_cache:
                flatctx: FlatContext = self.ctx_cache[after.id]

                if flatctx.cleanup_on_edit:
                    if after.id in self.active_contexts and self.active_contexts[after.id].tasks:
                        ctx = self.active_contexts[after.id]
                        for task in ctx.tasks:
                            task.cancel()

                        await asyncio.gather(*ctx.tasks, return_exceptions=True)
                        cleanup_task = asyncio.ensure_future(self.active_command_response_cleaner(ctx))
                        ctx.tasks.append(cleanup_task)
                    else:
                        cleanup_task = asyncio.ensure_future(self.flat_command_response_cleaner(flatctx))

                if flatctx.reparse_on_edit:
                    await self.parse_message(after)
            else:
                await self.on_message(after)

    async def flat_command_response_cleaner(self, flatctx: FlatContext):
        ch = self.get_channel(flatctx.ch)
        if ch is not None:
            for msgid in flatctx.sent_messages:
                with suppress(Exception):
                    msg = await ch.fetch_message(msgid)
                    await msg.delete()

    async def active_command_response_cleaner(self, ctx: Context):
        with suppress(discord.NotFound):
            if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                await ctx.ch.delete_messages(ctx.sent_messages)
            else:
                await asyncio.gather(*(msg.delete() for msg in ctx.sent_messages))

    async def parse_message(self, message):
        """
        Parse incoming messages.
        If the message contains a valid command, pass the message to run_cmd
        """
        content = message.content.strip()

        # get prefixes
        prefixes: tuple[str, ...] = await self.valid_prefixes(message)
        prefixes = tuple(prefix for prefix in prefixes if content.startswith(prefix))

        for prefix in sorted(prefixes, reverse=True):
            # If the message starts with a valid command, pass it along to run_cmd
            stripcontent: str = content[len(prefix) :].strip()
            cmdnames: list[str] = [
                cmdname for cmdname in self.cmd_names if stripcontent[: len(cmdname)].lower() == cmdname
            ]

            if cmdnames:
                cmdname: str = max(cmdnames, key=len)
                await self.run_cmd(message, cmdname, stripcontent[len(cmdname) :].strip(), prefix)
                return

        # Run the extra message parsers
        for parser in self.extra_message_parsers:
            task = asyncio.ensure_future(parser[0](self, message), loop=self.loop)
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

    async def run_cmd(self, message: Message, cmdname: str, arg_str: str, prefix: str):
        """
        Run a command and pass it the command message and the arg_str.

        Parameters
        ----------
        message: Message
            The original command message.
        cmdname: str
            The name of the command to execute.
        arg_str: str
            The remaining content of the command message after the prefix and command name.
        prefix: str
            Prefix used in invoking the command
        """

        cmd: Command = self.cmd_names[cmdname]
        content: str = "\n".join("\t" + line for line in message.content.splitlines())

        log(
            f"cmd: {cmdname} ({cmd.module.name})\nusr: {message.author} ({message.author.id})\ncid: {'DM' if message.channel.id == LUATEXIT_ID else message.channel} ({'' if message.channel.id == LUATEXIT_ID else message.channel.id})\ngid: {message.guild or ''} ({message.guild.id if message.guild else ''})\n\n{content}",
            context=f"{message.id}",
        )

        if not cmd.module.enabled:
            log("s     skip", context=f"{message.id}")
            self.update_cmdnames()

        if not cmd.module.ready.is_set():
            log(f"w     |-- waiting {cmd.module.name}", context=f"{message.id}")
            await cmd.module.ready.wait()

        # Build the context
        ctx: Context = self.baseContext(
            client=self,
            message=message,
            arg_str=arg_str,
            alias=cmdname,
            cmd=cmd,
            prefix=prefix,
        )

        # Add command to command cache and active contexts
        self.ctx_cache[message.id] = ctx.flatten()
        self.active_contexts[message.id] = ctx

        mid_token = current_mid.set(message.id)
        try:
            await cmd.run(ctx)
        except Exception:
            log(
                f"The following exception was encountered executing command '{cmdname}'.\n{traceback.format_exc()}",
                context=f"{message.id}",
                level=logging.ERROR,
            )
        finally:
            current_mid.reset(mid_token)
            self.ctx_cache[message.id] = ctx.flatten()
            self.active_contexts.pop(message.id, None)

    def load_dir(self, dirpath):
        """
        Import all modules in a directory.
        Primarily for the use of importing new commands.
        """
        loaded: int = 0
        initial_cmds: int = len(self.cmds)

        for fn in Path(dirpath).iterdir():
            if fn.is_file() and fn.suffix == ".py":
                path: Path = fn.absolute()
                module_name: str = "bot_module_" + str(fn)
                spec: importlib.machinery.ModuleSpec = importlib.util.spec_from_file_location(module_name, path)
                module: types.ModuleType = importlib.util.module_from_spec(spec)

                sys.path.append(dirpath)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                sys.path.remove(dirpath)

                if "load_into" in dir(module):
                    module.load_into(self)

                loaded += 1
        log(f"[load] {loaded} modules {dirpath} ({len(self.cmds) - initial_cmds} cmds)")

    def add_message_parser(self, func, priority=0):
        """
        Add a message parser to execute when the command message parser fails.

        Parameters
        ----------
        func: Function(Client, Message)
            Function taking the client and the discord message to process.
        priority: int
            Priority indiciating which order the parsers should be run.
            The command message parser is always executed first.
            After that, parsers are executed in order of increasing priority.
        """

        async def new_func(client, message):
            try:
                await func(client, message)
            except Exception:
                log(
                    "Exception encountered executing parser '{parser}' for a message "
                    "from user '{message.author}' (uid:{message.author.id}) "
                    "in guild '{message.guild}' (gid:{guildid}) "
                    "in channel '{message.channel}' (cid:{message.channel.id}).\n"
                    "Traceback:\n{traceback}\n"
                    "Content:\n{content}".format(
                        parser=func.__name__,
                        message=message,
                        guildid=message.guild.id if message.guild else None,
                        content="\n".join("\t" + line for line in message.content.splitlines()),
                        traceback="\n".join("\t" + line for line in traceback.format_exc().splitlines()),
                    ),
                    context=f"{message.id}",
                    level=logging.ERROR,
                )

        self.extra_message_parsers.insert(
            bisect([parser[1] for parser in self.extra_message_parsers], priority),
            (new_func, priority),
        )
        log(f"  |------{func.__name__} (priority: {priority})", level=logging.DEBUG)

    def add_after_event(self, event, func, priority=0):
        """
        Add an event handler to execute after the central event handler.

        Parameters
        ----------
        event: str
            Name of a valid discord.py event.
        func: Function(Client, ...)
            Function taking the client as its first argument, and the event parameters as the rest
        priority: int
            Priority indiciating which order the event handlers should be executed.
            The core event handler is always executed first.
            After that, handlers are executed in order of increasing priority.
        """

        async def new_func(*args, **kwargs):
            try:
                await func(*args, **kwargs)
            except Exception:
                log(
                    (
                        f"Exception encountered executing event handler '{func.__name__}' for event '{event}'. Traceback:\n{traceback.format_exc()}"
                    ),
                    level=logging.ERROR,
                )

        after_handler = "after_" + event
        if not hasattr(self, after_handler):
            setattr(self, after_handler, [])
        handlers = getattr(self, after_handler)
        handlers.insert(bisect([handler[1] for handler in handlers], priority), (new_func, priority))
        log(f"  |-- [event] {func.__name__} | {event} (prio: {priority})", level=logging.DEBUG)

    def dispatch(self, event, *args, **kwargs):
        super().dispatch(event, *args, **kwargs)
        after_handler = "after_" + event
        if hasattr(self, after_handler):
            for handler in getattr(self, after_handler):
                task = asyncio.ensure_future(handler[0](self, *args, **kwargs), loop=self.loop)
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)


cmd = cmdClient.cmd
