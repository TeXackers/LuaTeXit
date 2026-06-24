import asyncio
import logging
import textwrap
import traceback

from .Check import FailedCheck
from .lib import SafeCancellation, flag_parser
from .logger import log


class Command(object):
    def __init__(self, name, func, module, **kwargs):
        self.name = name
        self.func = func
        self.module = module

        self.handle_edits = kwargs.pop("handle_edits", True)

        self.aliases = kwargs.pop("aliases", [])
        self.flags = kwargs.pop("flags", [])
        self.hidden = kwargs.pop("hidden", False)
        self.short_help = kwargs.pop("short_help", None)
        self.long_help = self.parse_help()

        self.__dict__.update(kwargs)

    async def run(self, ctx):
        """
        Safely execute this command with the current context.
        Respond and log any exceptions that arise.
        """
        try:
            task = asyncio.ensure_future(self.exec_wrapper(ctx))
            ctx.tasks.append(task)
            await task
        except FailedCheck as e:
            log(
                "Command failed check: {}".format(e.check.name),
                context="mid:{}".format(ctx.msg.id),
                level=logging.DEBUG,
            )

            if e.check.msg:
                await ctx.error_reply(e.check.msg)
        except SafeCancellation as e:
            log(
                "Caught a safe command cancellation: {}: {}".format(
                    e.__class__.__name__, e.msg
                ),
                context="mid:{}".format(ctx.msg.id),
                level=logging.DEBUG,
            )

            if e.msg is not None:
                await ctx.error_reply(e.msg)
        except asyncio.TimeoutError:
            log(
                "Caught an unhandled TimeoutError",
                context="mid:{}".format(ctx.msg.id),
                level=logging.WARNING,
            )

            await ctx.error_reply("Operation timed out.")
        except asyncio.CancelledError:
            log(
                "Command was cancelled, probably due to a message edit.",
                context="mid:{}".format(ctx.msg.id),
                level=logging.DEBUG,
            )
        except Exception as e:
            full_traceback = traceback.format_exc()
            only_error = "".join(
                traceback.TracebackException.from_exception(e).format_exception_only()
            )

            log(
                "Caught the following exception while running command:\n{}".format(
                    full_traceback
                ),
                context="mid:{}".format(ctx.msg.id),
                level=logging.ERROR,
            )

            await ctx.reply(
                (
                    "An unexpected internal error occurred while running your command! "
                    "Please report the following error to the developer:\n`{}`"
                ).format(only_error)
            )
        else:
            log(
                "Command completed execution without error.",
                context="mid:{}".format(ctx.msg.id),
                level=logging.DEBUG,
            )

    async def exec_wrapper(self, ctx):
        """
        Execute the command in the current context.
        May raise an exception if not handled by the module on_exception handler.
        """
        try:
            await self.module.pre_command(ctx)
            if self.flags:
                flags, ctx.args = flag_parser(ctx.arg_str, self.flags)
                await self.func(ctx, flags=flags)
            else:
                await self.func(ctx)
            await self.module.post_command(ctx)
        except Exception as e:
            await self.module.on_exception(ctx, e)

    def parse_help(self):
        """
        Convert the docstring of the command function into a list of (fieldname, fieldcontent) tuples.
        """
        if not self.func.__doc__:
            return []

        # Split the docstring into lines
        lines = textwrap.dedent(self.func.__doc__).strip().splitlines()
        help_fields = []
        field_name = ""
        field_content = []

        for line in lines:
            if line.endswith(":"):
                # New field!
                if field_content:
                    # Add the previous field to the table
                    field = textwrap.dedent("\n".join(field_content))
                    help_fields.append((field_name, field))

                # Initialise the new field
                field_name = line[:-1].strip()
                field_content = []
            else:
                # Add the line to the current field content
                field_content.append(line)

        # Add the last field to the table if it exists
        if field_content:
            # Add the previous field to the table
            field = textwrap.dedent("\n".join(field_content))
            help_fields.append((field_name, field))

        return help_fields
