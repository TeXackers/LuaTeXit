import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .cmdClient import cmdClient
    from .Context import Context

from .Command import Command
from .logger import log


class Module:
    """Data structure for a module of commands."""

    name: str = "Base Module"

    def __init__(self, name: str | None = None, baseCommand: type[Command] = Command) -> None:
        if name:
            self.name: str = name
        self.baseCommand: type[Command] = baseCommand

        self.cmds: list[Command] = []
        self.initialised: bool = False
        self.ready: asyncio.Event = asyncio.Event()
        self.enabled: bool = True

        self.launch_tasks: list[Callable] = []
        self.init_tasks: list[Callable] = []

        from .cmdClient import cmdClient  # noqa: PLC0415

        cmdClient.modules.append(self)

        log("     module", context=self.name, level=logging.DEBUG)

    def cmd(self, name, cmdClass: type[Command] | None = None, **kwargs) -> Callable[[Callable], Command]:
        """
        Decorator to create a command in this module with the given `name`.
        Creates the command using the provided `cmdClass`.
        Adds the command to the module command list and updates the client cache.
        Transparently passes the rest of the arguments to the `Command` constructor.
        """
        log(f"+     |-/{name}", context=self.name, level=logging.DEBUG)

        cmdClass = cmdClass or self.baseCommand

        def decorator(func: Callable) -> Command:
            from .cmdClient import cmdClient  # noqa: PLC0415

            cmd: Command = cmdClass(name, func, self, **kwargs)
            self.cmds.append(cmd)
            cmdClient.update_cmdnames()
            return cmd

        return decorator

    def attach(self, func: Callable) -> None:
        """
        Decorator which attaches the provided function to the current instance.
        """
        setattr(self, func.__name__, func)
        log(f"  |-- {func.__name__}", context=self.name, level=logging.DEBUG)

    def launch_task(self, func: Callable) -> Callable:
        """
        Decorator which adds a launch function to complete during the default launch procedure.
        """
        self.launch_tasks.append(func)
        log(f"  |-- {func.__name__}", context=self.name, level=logging.DEBUG)
        return func

    def init_task(self, func: Callable) -> Callable:
        """
        Decorator which adds an init function to complete during the default initialise procedure.
        """
        self.init_tasks.append(func)
        log(f"  |-- {func.__name__}", context=self.name, level=logging.DEBUG)
        return func

    def initialise(self, client: cmdClient) -> None:
        """
        Initialise hook.
        Executed by `client.initialise_modules`,
        or possibly by modules which depend on this one.
        """
        if not self.initialised:
            if self.init_tasks:
                names = ", ".join(task.__name__ for task in self.init_tasks)
                log(f"task init: {names}", context=self.name, level=logging.DEBUG)
            else:
                log("task init", context=self.name, level=logging.DEBUG)

            for task in self.init_tasks:
                task(client)

            self.initialised = True
        else:
            log("  |-- skipped", context=self.name, level=logging.DEBUG)

    async def launch(self, client: cmdClient) -> None:
        """
        Launch hook.
        Executed in `client.on_ready`.
        Must set `ready` to `True`, otherwise all commands will hang.
        """
        if not self.ready.is_set():
            if self.launch_tasks:
                names = ", ".join(task.__name__ for task in self.launch_tasks)
                log(f"ready: {names}", context=self.name, level=logging.DEBUG)
            else:
                log("ready", context=self.name, level=logging.DEBUG)

            for task in self.launch_tasks:
                await task(client)

            self.ready.set()
        else:
            log("  |-- skipped", context=self.name, level=logging.DEBUG)

    async def pre_command(self, ctx: Context):
        """
        Pre-command hook.
        Executed before a command is run.
        """

    async def post_command(self, ctx: Context):
        """
        Post-command hook.
        Executed after a command is run without exception.
        """

    async def on_exception(self, ctx: Context, exception: Exception):
        """
        Exception hook.
        Executed when a command function throws an exception.
        This is executed before "standard" exceptions are caught.
        """
        raise exception
