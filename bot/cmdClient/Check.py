from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .Context import Context


class Check:
    """
    A `check` to be executed during or before command execution.

    Parameters
    ----------
    name: str
        Name of the check to use in logs.
    msg: str
        The string to post when a check fails before a command.
    check_func: function
        The check function used to evaluate the check.
        This must take a `Context` as the first argument.
        It must accept arbitrary arguments and keyword arguments.
        It must return `True` if the check passed, and `False` if the check failed.
    parents: List[Check]
        A list of `Checks` which superscede the current check.
        Precisely, if one of the parent checks pass, this check will also pass.
    requires: List[Check]
        A list of `Checks` required by the current check.
        All of these checks must pass for the current check to pass.
        These are checked after the parents.
    """

    def __init__(
        self,
        name: str,
        msg: str,
        check_func: Callable[..., Awaitable[bool]],
        parents: list[Check] | None = None,
        requires: list[Check] | None = None,
    ):
        self.name = name
        self.msg = msg
        self.check_func: Callable[..., Awaitable[bool]] = check_func

        self.parents = parents or []
        self.required = requires or []

    def __call__(self, *args, **kwargs) -> Callable[[Callable], Callable]:
        """
        Returns a function decorator which adds this check before the function.
        Throws FailedCheck if the check fails.
        """

        def decorator(func):
            @wraps(func)
            async def wrapper(ctx: type[Context], *fargs, **fkargs):
                result: bool = await self.run(ctx, *args, **kwargs)
                if not result:
                    raise FailedCheck(self)

                return await func(ctx, *fargs, **fkargs)

            return wrapper

        return decorator

    async def run(self, ctx: type[Context], *args, **kwargs) -> bool:
        """
        Executes this check and returns `True` if it passes or `False` if it fails.
        """
        # First check the parents
        for check in self.parents:
            if await check.run(ctx, *args, **kwargs):
                return True

        # Then check the requirements
        for check in self.required:
            if not await check.run(ctx, *args, **kwargs):
                return False

        # Now if we have passed all these, check the main function
        return await self.check_func(ctx, *args, **kwargs)


class FailedCheck(Exception):
    """
    Custom exception to throw when a pre-command check fails.
    Stores the check which failed.
    """

    def __init__(self, check: Check):
        super().__init__()

        self.check: Check = check


def check(*args, **kwargs) -> Callable[[Callable[..., Awaitable[bool]]], Check]:
    """
    Helper decorator for creating new checks.
    All arguments are passed to `Check` along with the decorated function as `check_func`.
    """

    def decorator(func: Callable[..., Awaitable[bool]]) -> Check:
        return Check(check_func=func, *args, **kwargs)

    return decorator
