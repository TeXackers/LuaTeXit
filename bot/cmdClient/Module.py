from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .Context import Context

from . import cmdClient
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
        self.ready: bool = False
        self.enabled: bool = True

        self.launch_tasks: list[Callable] = []
        self.init_tasks: list[Callable] = []

        cmdClient.cmdClient.modules.append(self)

        log("     module", context=self.name)

    def cmd(self, name, cmdClass: type[Command] | None = None, **kwargs) -> Callable[[Callable], Command]:
        """
        Decorator to create a command in this module with the given `name`.
        Creates the command using the provided `cmdClass`.
        Adds the command to the module command list and updates the client cache.
        Transparently passes the rest of the arguments to the `Command` constructor.
        """
        log(f"+     |-/{name}", context=self.name)

        cmdClass = cmdClass or self.baseCommand

        def decorator(func: Callable) -> Command:
            cmd: Command = cmdClass(name, func, self, **kwargs)
            self.cmds.append(cmd)
            cmdClient.cmdClient.update_cmdnames()
            return cmd

        return decorator

    def attach(self, func: Callable) -> None:
        """
        Decorator which attaches the provided function to the current instance.
        """
        setattr(self, func.__name__, func)
        log(f"+     |--[attach] {func.__name__}", context=self.name)

    def launch_task(self, func: Callable) -> Callable:
        """
        Decorator which adds a launch function to complete during the default launch procedure.
        """
        self.launch_tasks.append(func)
        log(f"t     |--[task] {func.__name__}", context=self.name)
        return func

    def init_task(self, func: Callable) -> Callable:
        """
        Decorator which adds an init function to complete during the default initialise procedure.
        """
        self.init_tasks.append(func)
        log(f"i     |--[init] {func.__name__}", context=self.name)
        return func

    def initialise(self, client: cmdClient.cmdClient) -> None:
        """
        Initialise hook.
        Executed by `client.initialise_modules`,
        or possibly by modules which depend on this one.
        """
        if not self.initialised:
            log("      task init", context=self.name)

            for task in self.init_tasks:
                log(f"t     |--[task] {task.__name__}", context=self.name)
                task(client)

            self.initialised = True
        else:
            log("s     |--[skip]", context=self.name)

    async def launch(self, client: cmdClient.cmdClient) -> None:
        """
        Launch hook.
        Executed in `client.on_ready`.
        Must set `ready` to `True`, otherwise all commands will hang.
        """
        if not self.ready:
            log("launching", context=self.name)

            for task in self.launch_tasks:
                log(f"t     |--[task] {task.__name__}", context=self.name)
                await task(client)

            self.ready = True
        else:
            log("s     |--[skip]", context=self.name)

    async def pre_command(self, ctx: type[Context]):
        """
        Pre-command hook.
        Executed before a command is run.
        """
        pass

    async def post_command(self, ctx: type[Context]):
        """
        Post-command hook.
        Executed after a command is run without exception.
        """
        pass

    async def on_exception(self, ctx: type[Context], exception: Exception):
        """
        Exception hook.
        Executed when a command function throws an exception.
        This is executed before "standard" exceptions are caught.
        """
        raise exception
        pass
