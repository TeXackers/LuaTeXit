import logging

logger = logging.getLogger()


def _log(message, context="Global".center(20, " "), level=logging.INFO):
    for line in message.split("\n"):
        logger.log(level, "[{}] {}".format(str(context).center(22, " "), line))


def log(*args, **kwargs):
    _log(*args, **kwargs)


def cmd_log_handler(func):
    global _log
    _log = func
    return func
