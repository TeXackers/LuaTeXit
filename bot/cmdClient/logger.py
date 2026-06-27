import logging
from collections.abc import Callable  # noqa

logger = logging.getLogger()


def _log(message: str, context: str = "Global", level: int = logging.INFO) -> None:
    for line in message.split("\n"):
        logger.log(level, f"[{str(context).center(22, ' ')}] {line}")


def log(*args, **kwargs):
    _log(*args, **kwargs)


def cmd_log_handler(func: Callable[..., None]) -> Callable[..., None]:
    global _log
    _log = func
    return func
