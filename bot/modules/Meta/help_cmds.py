import asyncio
from typing import TYPE_CHECKING

import discord
from cmdClient import Context  # noqa
from constants import sorted_cats
from utils import ctx_addons  # noqa
from utils.lib import prop_tabulate
from wards import is_manager

if TYPE_CHECKING:
    from bot.modules import Module

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

        Using the `man` alias will automatically show the full help embed.
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
                f"and `{await ctx.best_prefix()}help cmd` to get detailed help on a command!"
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
                    f"The full command list may be found using `{await ctx.best_prefix()}list`."
                )
            # If this was triggered by the `h` alias, don't respond unless there's a space afterwards
            if ctx.alias == "h":
                true_args = ctx.msg.content.strip()[len(ctx.prefix) :].strip()[1:]
                if not true_args or true_args[0] not in (" ", "\n"):
                    return None

            return await ctx.error_reply(
                f"Command `{ctx.arg_str}` not found!\n"
                f"Use the `{await ctx.best_prefix()}list` command without arguments to see a list of commands."
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
                # Handle property/value help fields
                lines = help_fields[pos][1].splitlines()

                names = []
                values = []
                for line in lines:
                    split = line.split(":", 1)
                    names.append(split[0] if len(split) > 1 else "")
                    values.append(split[-1])

                help_fields[pos] = (name.strip(":"), prop_tabulate(names, values))
            elif name == "Related":
                # Handle the related field
                names = [cmd_name.strip() for cmd_name in help_fields[pos][1].split(",")]
                names.sort(key=len)
                values = [getattr(ctx.client.cmd_names.get(cmd_name, None), "desc", "") for cmd_name in names]
                help_fields[pos] = (name, prop_tabulate(names, values))

        # Create command alias string for title
        aliases = getattr(command, "aliases", [])
        alias_str = "(Alias{} `{}`.)".format("es" if len(aliases) > 1 else "", "`, `".join(aliases)) if aliases else ""

        # Build the help embed
        embed = discord.Embed(
            title=f"`{command.name}` command documentation. {alias_str}", colour=discord.Colour(0x9B59B6)
        )
        out_msg = None

        if (
            ctx.alias.lower() != "man"
            and len(help_fields) > 2
            and sum(len(field[1].splitlines()) for field in help_fields) > 15
            and (
                not ctx.guild
                or (
                    ctx.ch.permissions_for(ctx.guild.me).add_reactions
                    and ctx.ch.permissions_for(ctx.guild.me).use_external_emojis
                )
            )
        ):
            # Show a "short" version of the help with a `MORE` reaction.
            more_emoji = ctx.client.conf.emojis.getemoji("more")
            embed.description = f"{command.desc}"

            for fieldname, fieldvalue in help_fields:
                if fieldname in ["Usage"]:
                    # Format the field
                    fieldvalue = fieldvalue.format(ctx=ctx, prefix=ctx.client.prefix)
                    fieldvalue += f"\n\nClick {more_emoji} to show more information."

                    embed.add_field(name=fieldname, value=fieldvalue, inline=False)
            out_msg = await ctx.reply(embed=embed)
            asyncio.ensure_future(ctx.offer_delete(out_msg))
            await out_msg.add_reaction(more_emoji)
            try:
                await ctx.client.wait_for(
                    "reaction_add",
                    check=lambda r, u: r.emoji == more_emoji and r.message == out_msg and u != ctx.client.user,
                    timeout=300,
                )
            except asyncio.TimeoutError:
                return None
            finally:
                # Clean up
                try:
                    if ctx.guild and ctx.ch.permissions_for(ctx.guild.me).manage_messages:
                        await out_msg.clear_reaction(more_emoji)
                    else:
                        await out_msg.remove_reaction(more_emoji, ctx.client.user)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
            embed.description = None
            embed.remove_field(0)

        for fieldname, fieldvalue in help_fields:
            # Format the field
            fieldvalue = fieldvalue.format(ctx=ctx, prefix=ctx.client.prefix)

            embed.add_field(name=fieldname, value=fieldvalue, inline=False)

        # Add the support guild invite
        embed.add_field(
            name="Have more questions?",
            value=f"Visit our support server [here]({ctx.client.app_info['support_guild']}) to speak to our friendly support team!",
        )

        embed.set_footer(text="[optional] and <required> denote optional and required arguments, respectively.")

        # Post the embed
        if out_msg:
            return await out_msg.edit(embed=embed)
        return await ctx.offer_delete(await ctx.reply(embed=embed))
        # await ctx.offer_delete(await ctx.reply(embed=embed))
    return None


@module.cmd("list", desc="Lists all my commands!", aliases=["ls"])
async def cmd_list(ctx: Context) -> None:
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
    show_hidden: bool = await is_manager.run(ctx)
    modules: list[type[Module]] = [
        module for module in ctx.client.modules if module.enabled and (show_hidden or not module.hidden)
    ]

    if ctx.alias.lower() == "ls":
        # Make the cats (category/module command lists)
        cats = {cat.name.lower(): sorted(cat.cmds, key=lambda cmd: cmd.name) for cat in modules}

        # Build brief listing embed
        embed = discord.Embed(title="My commands!", color=discord.Colour.green())
        # Construct embed fields from the cats in the order of sorted_cats
        for cat in sorted_cats:
            if cat.lower() in cats:
                embed.add_field(
                    name=cat,
                    value=", ".join(
                        f"~~`{cmd.name}`~~" if cmd.disabled else f"`{cmd.name}`"
                        for cmd in cats[cat.lower()]
                        if (show_hidden or not cmd.hidden)
                    ),
                    inline=False,
                )
        embed.set_footer(
            text="Use '{0}help' or '{0}help cmd' for detailed help, or get support with {0}support.".format(
                await ctx.best_prefix()
            )
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

        # Build the command groups
        groups = {
            cat.name: (
                cat,
                [
                    (cmd.name, getattr(cmd, "desc", f"See `{await ctx.best_prefix()}help {cmd.name}`."), cmd)
                    for cmd in sorted(cat.cmds, key=lambda cmd: len(cmd.name))
                    if (show_hidden or not cmd.hidden)
                ],
            )
            for cat in modules
            if (not ctx.args or (ctx.args.lower() in cat.name.lower()))
        }

        if not groups:
            return await ctx.error_reply(
                f"No matching modules! See `{await ctx.best_prefix()}ls` for a list of modules and their commands."
            )

        # Sort the command groups based on sorted_cats and extract the required data
        # stringy_groups = [(groups[catname][0], prop_tabulate(*zip(*groups[catname][1][:2])))
        #                   for catname in sorted_cats if catname in groups]
        # Quick hack to handle disabled commands
        stringy_groups = []
        for catname in sorted_cats:
            if catname in groups:
                cat = groups[catname][0]
                try:
                    props, values, commands = zip(*groups[catname][1])
                    table = prop_tabulate(props, values)
                    table = "\n".join(
                        ("~~{}~~" if commands[i].disabled else "{}").format(line)
                        for i, line in enumerate(table.splitlines())
                    )
                    stringy_groups.append((cat, table))
                except ValueError:
                    continue

        # Now put everything into embeds
        help_embeds = []  # List of embed pages to respond with
        current_page_fields = []  # Buffer list of current fields before making a page
        current_page_len = 0  # Current length of the page being built
        for cat, catstr in stringy_groups:
            # Create new field
            new_field = (cat.name, cat.description + "\n" + catstr)
            if current_page_len + len(new_field[1]) > 1000:
                # Flush to a new page
                # Create the embed
                embed = discord.Embed(description=help_str, colour=discord.Colour(0x9B59B6), title=help_title)
                for name, field in current_page_fields:
                    embed.add_field(name=name, value=field, inline=False)

                # Add the embed to the pages list
                help_embeds.append(embed)

                # Flush page trackers
                current_page_fields = []
                current_page_len = 0

            # Add to current page and continue
            current_page_fields.append(new_field)
            current_page_len += len(new_field[1])

        # If there is anything left, add it as the last page
        if current_page_fields:
            # Create the embed
            embed = discord.Embed(description=help_str, colour=discord.Colour(0x9B59B6), title=help_title)
            for name, field in current_page_fields:
                embed.add_field(name=name, value=field, inline=False)

            # Add the embed to the pages list
            help_embeds.append(embed)

        # Add the page numbers
        for i, embed in enumerate(help_embeds):
            embed.set_footer(text=f"Page {i + 1}/{len(help_embeds)}")

        # Send the embeds
        return await ctx.offer_delete(await ctx.pager(help_embeds))
    return None
