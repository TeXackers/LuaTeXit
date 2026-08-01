from typing import TYPE_CHECKING

import discord
from cmdClient import Context
from constants import sorted_cats
from utils.lib import tabulate
from wards import is_admin

if TYPE_CHECKING:
    from modules import Module

from .module import meta_module as module

"""
Commands to obtain usage information for the bot and commands.

Commands provided:
    help:
        Sends the bot help message or detailed help on a command.
    list:
        Sends the list of commands in either a brief or expanded form.
"""


@module.cmd("help", desc="Bot and command usage information.", aliases=["h", "man"])
async def cmd_help(ctx: Context):
    """
    Usage``:
        {prefix}help [command name]
    Description:
        Shows detailed usage information for the requested command or sends you the general help message.
    Related:
        list
    Example``:
        {prefix}help
        {prefix}help help
    """
    if not ctx.args:
        # Send general bot help
        help_msg = ctx.client.app_info["help_str"].format(
            prefix=ctx.client.prefix,
            user=ctx.author,
            invite=ctx.client.app_info["invite_link"],
            support=ctx.client.app_info["support_guild"],
            donate=ctx.client.app_info["donate_link"],
            github=ctx.client.app_info["github"],
        )
        help_filename = ctx.client.app_info.get("help_file", None)
        help_file = discord.File(help_filename) if help_filename else None
        help_embed = ctx.client.app_info.get("help_embed", None)

        await ctx.dm_reply(help_msg, file=help_file, embed=help_embed)
        if ctx.ch.type != discord.ChannelType.private:
            await ctx.reply(
                "A brief description and guide on how to use me was sent to your DMs!\n"
                f"Please use `{await ctx.best_prefix()}list` to see a list of all my commands, "
                f"and `{await ctx.best_prefix()}help cmd` to get detailed help on a command!",
            )
    else:
        # Send specific command help

        # Attempt to fetch the command
        command = ctx.client.cmd_names.get(ctx.args.strip(), None)
        if command is None:
            if ctx.args == "cmd":
                return await ctx.reply(
                    "~~You really shouldn't take it literally :upside_down:.~~ "
                    f"Please type `{await ctx.best_prefix()}help ping`, for example!\n"
                    f"The full command list may be found using `{await ctx.best_prefix()}list`.",
                )
            # If this was triggered by the `h` alias, don't respond unless there's a space afterwards
            if ctx.alias == "h":
                true_args = ctx.msg.content.strip()[len(ctx.prefix) :].strip()[1:]
                if not true_args or true_args[0] not in (" ", "\n"):
                    return None

            return await ctx.error_reply(
                f"Command `{ctx.arg_str}` not found!\n"
                f"Use the `{await ctx.best_prefix()}list` command without arguments to see a list of commands.",
            )

        help_fields = command.long_help.copy()
        help_map = {field_name: i for i, (field_name, _) in enumerate(help_fields)}

        if not help_map:
            return await ctx.reply("No documentation has been written for this command yet!")

        for name, pos in help_map.items():
            if name.endswith("``"):
                # Handle codeline help fields
                help_fields[pos] = (name.strip("`"), "`{}`".format("`\n`".join(help_fields[pos][1].splitlines())))
            elif name.endswith(":"):
                # Handle property/value help fields; a line with no colon is a wrapped
                # continuation of the previous property's value (e.g. guildpreamble_cmd.py).
                props: dict[str, str] = {}
                last_prop = None
                for line in help_fields[pos][1].splitlines():
                    prop, sep, value = line.partition(":")
                    if sep:
                        last_prop = prop
                        props[last_prop] = value.strip()
                    elif last_prop is not None:
                        props[last_prop] += f" {line.strip()}"
                help_fields[pos] = (name.strip(":"), tabulate(props))
            elif name == "Related":
                # Handle the related field
                names = sorted((cmd_name.strip() for cmd_name in help_fields[pos][1].split(",")), key=len)
                props = {n: getattr(ctx.client.cmd_names.get(n, None), "desc", "") for n in names}
                help_fields[pos] = (name, tabulate(props))

        # Create command alias string for title
        aliases = getattr(command, "aliases", [])
        alias_str = "(Alias{} `{}`.)".format("es" if len(aliases) > 1 else "", "`, `".join(aliases)) if aliases else ""
        title = f"`{command.name}` command documentation. {alias_str}"

        # Build the help body: one markdown section per field, paged via components
        # instead of a classic embed, since e.g. a `Flags:` field with enough flags
        # (prop_tabulate-formatted) can easily exceed discord.Embed's 1024-char field limit.
        sections = [
            f"### {fieldname}\n{fieldvalue.format(ctx=ctx, prefix=ctx.client.prefix)}"
            for fieldname, fieldvalue in help_fields
        ]
        sections.append(
            "### Have more questions?\n"
            f"Visit our support server [here]({ctx.client.app_info['support_guild']}) "
            "to speak to our friendly support team!",
        )
        sections.append("-# [optional] and <required> denote optional and required arguments, respectively.")

        return await ctx.pager_v2("\n".join(sections), title=title, colour=discord.Colour(0x9B59B6))
    return None


@module.cmd("list", desc="Lists all my commands!", aliases=["ls"])
async def cmd_list(ctx: Context):
    """
    Usage``:
        {prefix}list [module]
        {prefix}ls
    Description:
        Provides a paged list of my commands with brief descriptions.
        When used as `ls`, provides a briefer single-page listing without descriptions..
    Arguments::
        module: Show only commands from this module.
    Related:
        help
    """
    # Flag for whether we display hidden modules in the list or not
    show_hidden: bool = await is_admin.run(ctx)
    modules: list[Module] = [
        module for module in ctx.client.modules if module.enabled and (show_hidden or not module.hidden)
    ]

    cat_order = {name: i for i, name in enumerate(sorted_cats)}
    ordered_modules = sorted(modules, key=lambda m: (cat_order.get(m.name, len(sorted_cats)), m.name))

    if ctx.alias.lower() == "ls":
        # Build brief listing embed
        embed = discord.Embed(title="My commands!", color=discord.Colour.green())
        for cat in ordered_modules:
            visible_cmds = sorted(
                (cmd for cmd in cat.cmds if (show_hidden or not cmd.hidden)),
                key=lambda cmd: cmd.name,
            )
            if not visible_cmds:
                continue
            embed.add_field(
                name=cat.name,
                value=", ".join(f"~~`{cmd.name}`~~" if cmd.disabled else f"`{cmd.name}`" for cmd in visible_cmds),
                inline=False,
            )
        embed.set_footer(
            text="Use '{0}help' or '{0}help cmd' for detailed help, or get support with {0}support.".format(
                await ctx.best_prefix(),
            ),
        )

        # Send the command list
        await ctx.offer_delete(await ctx.reply(embed=embed))
    else:
        # Handle long response format
        help_title = "My commands!"  # Title of detailed list embed
        help_str = (
            "Use `{0}ls` to obtain a briefer listing, and use `{0}help <cmd>`"
            "to view detailed help for a particular command, "
            "or `{0}help` to view general help.\n\n"
            "If you still have questions, talk to our friendly support team [here]({1})."
        ).format(await ctx.best_prefix(), ctx.client.app_info["support_guild"])

        # Build the command groups, restricted to modules matching the requested filter (if any)
        filtered_modules = [cat for cat in ordered_modules if (not ctx.args or (ctx.args.lower() in cat.name.lower()))]

        if not filtered_modules:
            return await ctx.error_reply(
                f"No matching modules! See `{await ctx.best_prefix()}ls` for a list of modules and their commands.",
            )

        # Build the stringy command tables, skipping modules with no visible commands
        sections = [help_str]
        for cat in filtered_modules:
            cmd_rows = [
                (cmd.name, getattr(cmd, "desc", f"See `{await ctx.best_prefix()}help {cmd.name}`."), cmd)
                for cmd in sorted(cat.cmds, key=lambda cmd: len(cmd.name))
                if (show_hidden or not cmd.hidden)
            ]
            if not cmd_rows:
                continue
            names, descs, commands = zip(*cmd_rows, strict=True)
            table = tabulate(dict(zip(names, descs, strict=True)))
            table = "\n".join(
                ("~~{}~~" if commands[i].disabled else "{}").format(line) for i, line in enumerate(table.splitlines())
            )
            sections.append(f"### {cat.name}\n{cat.description}\n{table}")

        return await ctx.pager_v2("\n".join(sections), title=help_title, colour=discord.Colour(0x9B59B6))
    return None
