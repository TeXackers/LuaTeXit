import asyncio
import logging
import traceback
from collections.abc import Callable  # noqa

import discord
from cmdClient import Context, Module, cmdClient
from cmdClient.Check import FailedCheck
from cmdClient.Layouts import DebugEmbedView
from cmdClient.lib import SafeCancellation
from logger import log
from settings import guild_config


class paraModule(Module):
    name = "Base module"

    def __init__(self, *args, description=None, hidden=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = description or "Paradox module"
        self.hidden = hidden

        self.data_init_tasks = []
        self.data_initialised = False

        self.guild_settings = []

        self.baseCommand.hidden = False
        self.baseCommand.disabled = False

    def guild_setting(self, cls):
        """
        Class decorator to attach a guild setting
        which will be later loaded on initialisation.
        """
        self.guild_settings.append(cls)
        log(f"+     |-/{cls.attr_name}", context=self.name)
        return cls

    def initialise(self, client: cmdClient):
        if self.guild_settings and not self.initialised:
            log("guild", context=self.name)
            for setting in self.guild_settings:
                log(f"+     |--{setting.attr_name}", context=self.name)
                guild_config.attach_setting(setting)
                setting.initialise(client)

        # Caches we expect
        if "disabled_guild_commands" not in client.objects:
            client.objects["disabled_guild_commands"] = {}
        if "disabled_guild_channels" not in client.objects:
            client.objects["disabled_guild_channels"] = {}

        super().initialise(client)

    async def pre_command(self, ctx: Context):
        if ctx.guild:
            disabled = ctx.client.objects["disabled_guild_commands"]
            if (
                ctx.guild.id in disabled
                and ctx.cmd.name in disabled[ctx.guild.id]
                and not ctx.author.guild_permissions.administrator
            ):
                raise SafeCancellation

            # Handle blacklisted guild channels
            disabled = ctx.client.objects["disabled_guild_channels"]
            if (
                ctx.guild.id in disabled
                and ctx.ch.id in disabled[ctx.guild.id]
                and not ctx.author.guild_permissions.administrator
            ):
                raise SafeCancellation

    def data_init_task(self, func: Callable[[cmdClient], None]) -> Callable[[cmdClient], None]:
        """
        Decorator which adds a data initialisation task.
        These tasks accept a client,
        but should not set up the client or assume any existing data or schema.
        The primary purpose is to attach the data interfaces for each module.
        """
        self.data_init_tasks.append(func)
        log(f"a     |--{func.__name__}", context=self.name)
        return func

    def initialise_data(self, client: cmdClient):
        """
        Data initialise hook.
        """
        if not self.data_initialised:
            log("data init", context=self.name)

            for task in self.data_init_tasks:
                log(f"t     |--[task] {task.__name__}", context=self.name)
                task(client)

            self.data_initialised = True
        else:
            log("s     |--[skip]", context=self.name)

    async def on_exception(self, ctx: Context, exception: Exception):
        try:
            raise exception
        except (FailedCheck, SafeCancellation) as e:
            # cmdClient generated and handled exceptions
            raise exception from e
        except (asyncio.CancelledError, asyncio.TimeoutError) as e:
            # Standard command and task exceptions, cmdClient will also handle these
            raise exception from e
        except discord.Forbidden:
            # Unknown uncaught Forbidden
            try:
                # Attempt a general error reply
                await ctx.error_reply("I don't have enough permissions here to complete the command!")
            except discord.Forbidden:
                # We can't send anything at all. Exit quietly, but log.
                full_traceback = traceback.format_exc()
                log(
                    (
                        "Caught an unhandled 'Forbidden' while "
                        f"executing command '{ctx.cmd.name}' from module '{ctx.cmd.module.name}' "
                        f"from user '{ctx.msg.author}' (uid:{ctx.msg.author.id}) "
                        f"in guild '{ctx.msg.guild}' (gid:{ctx.msg.guild.id if ctx.msg.guild else None}) "
                        f"in channel '{ctx.msg.channel}' (cid:{ctx.msg.channel.id}).\n"
                        "Message Content:\n"
                        f"{'\n'.join('\t' + line for line in ctx.msg.content.splitlines())}\n"
                        f"{full_traceback}\n\n"
                        f"{ctx.flatten()}"
                    ),
                    context=f"mid:{ctx.msg.id}",
                    level=logging.WARNING,
                )

        except Exception as e:
            # Unknown exception!
            full_traceback = traceback.format_exc()
            only_error = "".join(traceback.TracebackException.from_exception(e).format_exception_only())
            # Handle the error message being too long to display in the embed
            # Discord can throw error messages over the embed field limit
            if len(only_error) > 2000:
                only_error = only_error[:2000] + "..."

            log(
                (
                    "Caught an unhandled exception while "
                    "executing command '{cmdname}' from module '{module}' "
                    "from user '{message.author}' (uid:{message.author.id}) "
                    "in guild '{message.guild}' (gid:{guildid}) "
                    "in channel '{message.channel}' (cid:{message.channel.id}).\n"
                    "Message Content:\n"
                    "{content}\n"
                    "Traceback:\n"
                    "{traceback}\n\n"
                    "{flat_ctx}"
                ).format(
                    cmdname=ctx.cmd.name if ctx.cmd is not None else None,
                    module=ctx.cmd.module.name if ctx.cmd is not None else None,
                    message=ctx.msg,
                    guildid=ctx.guild.id if ctx.guild else None,
                    content="\n".join("\t" + line for line in ctx.msg.content.splitlines()),
                    traceback="\n".join("\t" + line for line in full_traceback.splitlines()),
                    flat_ctx=ctx.flatten(),
                ),
                context=f"mid:{ctx.msg.id}",
                level=logging.ERROR,
            )
            # if logging.getLogger().getEffectiveLevel() < logging.INFO:
            error_embed = DebugEmbedView(
                f"Following error occurred while executing command `{ctx.cmd.name}` from `{ctx.cmd.module.name}`",
                only_error,
                discord.utils.format_dt(discord.utils.utcnow(), style="F"),
            )
            return await ctx.reply(view=error_embed)
            # else:
            #     return await ctx.error_reply(
            #         f"An unexpected internal error occurred while running your command! Please report the following error to the developer:\n`{only_error}`"
            #     )


cmdClient.baseModule = paraModule
