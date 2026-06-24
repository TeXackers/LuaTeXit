import asyncio
import imp
import itertools
import logging
import os
import sys
import traceback
from bisect import bisect
from typing import ClassVar, Optional, Type

import discord
from cachetools import LRUCache

from .Context import Context
from .logger import log
from .Module import Module


class cmdClient(discord.Client):
    prefix: Optional[str]

    baseModule: ClassVar[Type[Module]] = Module
    default_module: ClassVar[Module] = None

    modules = []  # List of loaded modules

    cmd_names = {}  # Command name cache, {cmdname: Command}, including aliases.

    def __init__(
        self, prefix=None, owners=None, ctx_cache=None, baseContext=Context, **kwargs
    ):
        super().__init__(**kwargs)
        self.prefix = prefix
        self.owners = owners or []
        self.objects = {}

        self.baseContext = Context  # type: Type[Context]

        self.ctx_cache = ctx_cache or LRUCache(
            1000
        )  # Previous Context cache, {messageid: ctxcache}
        self.active_contexts = {}  # Current active contexts, {messageid: ctx}

        self.extra_message_parsers = []

    @property
    def cmds(self):
        """
        A list of current available commands.
        """
        return list(
            itertools.chain(*[module.cmds for module in self.modules if module.enabled])
        )

    @classmethod
    def get_default_module(cls):
        """
        Returns the default module, instantiating it if it does not exist.
        """
        if cls.default_module is None:
            cls.default_module = cls.baseModule()
        return cls.default_module

    @classmethod
    def cmd(cls, *args, module: Optional[Module] = None, **kwargs):
        """
        Helper decorator to create a command with an optional module.
        If no module is specified, uses the class default module.
        """
        module = module or cls.get_default_module()
        return module.cmd(*args, **kwargs)

    @classmethod
    def update_cmdnames(cls):
        """
        Updates the command name cache.
        """
        cmds = {}
        for module in cls.modules:
            if module.enabled:
                for cmd in module.cmds:
                    cmds[cmd.name] = cmd
                    for alias in cmd.aliases:
                        cmds[alias] = cmd
        cls.cmd_names = cmds

    async def valid_prefixes(self, message):
        if self.prefix:
            return (self.prefix,)
        else:
            log(
                "No prefix set and no prefix function implemented.", level=logging.ERROR
            )
            await self.close()

    def set_valid_prefixes(self, func):
        setattr(self, "valid_prefixes", func.__get__(self))

    def initialise_modules(self):
        log("Initialising all client modules.")
        for module in self.modules:
            if module.enabled:
                module.initialise(self)

    async def launch_modules(self):
        log("Launching all client modules.")
        for module in self.modules:
            if module.enabled:
                await module.launch(self)

    async def on_ready(self):
        """
        Client has logged into discord and completed initialisation.
        Log a ready message with some basic statistics and info.
        """
        await self.launch_modules()

        ready_str = (
            "Logged in as {client.user}\n"
            "User id {client.user.id}\n"
            "Logged in to {guilds} guilds\n"
            "------------------------------\n"
            "Default prefix is '{prefix}'\n"
            "Loaded {commands} commands\n"
            "------------------------------\n"
            "Ready to take commands!\n"
        ).format(
            client=self,
            guilds=len(self.guilds),
            prefix=self.prefix,
            commands=len(self.cmds),
        )
        log(ready_str)

    async def on_error(self, event_method, *args, **kwargs):
        """
        An exception was caught in one of the event handlers.
        Log the exception with a traceback, and continue on.
        """
        log(
            "Ignoring exception in {}\n{}".format(event_method, traceback.format_exc()),
            level=logging.ERROR,
        )

    async def on_message(self, message):
        """
        Event handler for `message`.
        Intended to be overridden.
        """
        await self.parse_message(message)

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            if after.id in self.ctx_cache:
                flatctx = self.ctx_cache[after.id]
                # Cleanup if required
                if flatctx.cleanup_on_edit:
                    if (
                        after.id in self.active_contexts
                        and self.active_contexts[after.id].tasks
                    ):
                        ctx = self.active_contexts[after.id]
                        [task.cancel() for task in ctx.tasks]
                        # Wait for the task to be removed from active contexts
                        while after.id in self.active_contexts:
                            await asyncio.sleep(0.1)
                        asyncio.ensure_future(self.active_command_response_cleaner(ctx))
                    else:
                        asyncio.ensure_future(
                            self.flat_command_response_cleaner(flatctx)
                        )
                # Reparse if required
                if flatctx.reparse_on_edit:
                    await self.parse_message(after)
            else:
                # If the message isn't in cache, treat as a new message
                await self.on_message(after)

    async def flat_command_response_cleaner(self, flatctx):
        ch = self.get_channel(flatctx.ch)
        if ch is not None:
            for msgid in flatctx.sent_messages:
                try:
                    msg = await ch.fetch_message(msgid)
                    asyncio.ensure_future(msg.delete())
                except Exception:
                    pass

    async def active_command_response_cleaner(self, ctx):
        try:
            if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                await ctx.ch.delete_messages(ctx.sent_messages)
            else:
                await asyncio.gather(*(msg.delete() for msg in ctx.sent_messages))
        except discord.NotFound:
            pass

    async def parse_message(self, message):
        """
        Parse incoming messages.
        If the message contains a valid command, pass the message to run_cmd
        """
        content = message.content.strip()

        # Get valid prefixes
        prefixes = await self.valid_prefixes(message)

        # Check whether the message starts with a valid prefix
        prefixes = [prefix for prefix in prefixes if content.startswith(prefix)]
        if prefixes is not None:
            for prefix in sorted(prefixes, reverse=True):
                # If the message starts with a valid command, pass it along to run_cmd
                stripcontent = content[len(prefix) :].strip()
                cmdnames = [
                    cmdname
                    for cmdname in self.cmd_names
                    if stripcontent[: len(cmdname)].lower() == cmdname
                ]

                if cmdnames:
                    cmdname = max(cmdnames, key=len)
                    await self.run_cmd(
                        message, cmdname, stripcontent[len(cmdname) :].strip(), prefix
                    )
                    return

        # Run the extra message parsers
        for parser in self.extra_message_parsers:
            asyncio.ensure_future(parser[0](self, message), loop=self.loop)

    async def run_cmd(self, message, cmdname, arg_str, prefix):
        """
        Run a command and pass it the command message and the arg_str.

        Parameters
        ----------
        message: discord.Message
            The original command message.
        cmdname: str
            The name of the command to execute.
        arg_str: str
            The remaining content of the command message after the prefix and command name.
        """
        cmd = self.cmd_names[cmdname]
        log(
            (
                "Executing command '{cmdname}' from module '{module}' "
                "from user '{message.author}' (uid:{message.author.id}) "
                "in guild '{message.guild}' (gid:{guildid}) "
                "in channel '{message.channel}' (cid:{message.channel.id}).\n"
                "{content}"
            ).format(
                cmdname=cmdname,
                module=cmd.module.name,
                message=message,
                guildid=message.guild.id if message.guild else None,
                content="\n".join(
                    ("\t" + line for line in message.content.splitlines())
                ),
            ),
            context="mid:{}".format(message.id),
        )

        if not cmd.module.enabled:
            log(
                "Skipping command due to disabled module.",
                context="mid:{}".format(message.id),
            )
            self.update_cmdnames()

        if not cmd.module.ready:
            log(
                "Waiting for module '{}' to be ready.".format(cmd.module.name),
                context="mid:{}".format(message.id),
            )
            while not cmd.module.ready:
                await asyncio.sleep(1)

        # Build the context
        ctx = self.baseContext(
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
        try:
            await cmd.run(ctx)
        except Exception:
            log(
                "The following exception was encountered executing command '{}'.\n{}".format(
                    cmdname, traceback.format_exc()
                ),
                context="mid:{}".format(message.id),
                level=logging.ERROR,
            )
        finally:
            # Renew command in command cache
            self.ctx_cache[message.id] = ctx.flatten()

            # Remove message from active contexts
            self.active_contexts.pop(message.id, None)

    def load_dir(self, dirpath):
        """
        Import all modules in a directory.
        Primarily for the use of importing new commands.
        """
        loaded = 0
        initial_cmds = len(self.cmds)

        for fn in os.listdir(dirpath):
            path = os.path.join(dirpath, fn)
            if fn.endswith(".py"):
                sys.path.append(dirpath)
                module = imp.load_source("bot_module_" + str(fn), path)
                sys.path.remove(dirpath)

                if "load_into" in dir(module):
                    module.load_into(self)

                loaded += 1
        log(
            "Imported {} modules from '{}', with {} new commands!".format(
                loaded, dirpath, len(self.cmds) - initial_cmds
            )
        )

    def add_message_parser(self, func, priority=0):
        """
        Add a message parser to execute when the command message parser fails.

        Parameters
        ----------
        func: Function(Client, discord.Message)
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
                        content="\n".join(
                            ("\t" + line for line in message.content.splitlines())
                        ),
                        traceback="\n".join(
                            (
                                "\t" + line
                                for line in traceback.format_exc().splitlines()
                            )
                        ),
                    ),
                    context="mid:{}".format(message.id),
                    level=logging.ERROR,
                )

        self.extra_message_parsers.insert(
            bisect([parser[1] for parser in self.extra_message_parsers], priority),
            (new_func, priority),
        )
        log(
            'Adding message parser "{}" with priority "{}"'.format(
                func.__name__, priority
            )
        )

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
                        "Exception encountered executing event handler '{}' for event '{}'. "
                        "Traceback:\n{}"
                    ).format(func.__name__, event, traceback.format_exc()),
                    level=logging.ERROR,
                )

        after_handler = "after_" + event
        if not hasattr(self, after_handler):
            setattr(self, after_handler, [])
        handlers = getattr(self, after_handler)
        handlers.insert(
            bisect([handler[1] for handler in handlers], priority), (new_func, priority)
        )
        log(
            'Adding after_event handler "{}" for event "{}" with priority "{}"'.format(
                func.__name__, event, priority
            )
        )

    def dispatch(self, event, *args, **kwargs):
        super().dispatch(event, *args, **kwargs)
        after_handler = "after_" + event
        if hasattr(self, after_handler):
            for handler in getattr(self, after_handler):
                asyncio.ensure_future(handler[0](self, *args, **kwargs), loop=self.loop)


cmd = cmdClient.cmd
