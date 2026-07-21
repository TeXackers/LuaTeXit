import datetime

import discord
from cmdClient import Context  # noqa
from constants import LuaTeXitCC
from utils.lib import prop_tabulate

from .core.TypstUser import TypstUser
from .module import typst_module as module
from .resources import default_preamble


@module.cmd("typstconfig", desc="View or modify your personal Typst rendering options.", aliases=["tyc"])
async def cmd_typstconfig(ctx: Context) -> None:
    """
    Usage``:
        {prefix}typstconfig
        {prefix}typstconfig help
        {prefix}typstconfig <setting>
        {prefix}typstconfig <setting> <value>
    Description:
        Configuration interface to view and modify the various options affecting your Typst compilation. These are *personal* configuration options.

        When used with no arguments, displays your current configuration.

        When used with `help`, displays brief descriptions of each option.

        When used with a `setting`, displays detailed information
        about that setting, or sets the setting to the provided `value`.

        `namestyle` and `colour` are shared with LaTeX, so setting them here also changes them for `{prefix}tex`, and vice versa.
    Related:
        autotypst, typstpreamble, typst
    Setting Examples``:
        {prefix}typstconfig colour dark
        {prefix}typstconfig autotypst on
        {prefix}typstconfig namestyle MENTION
    """
    # Build the typst user
    tuser = TypstUser.get(ctx.author.id)

    if not ctx.args or ctx.args.lower() == "help":
        # Display the configuration options with either values or the descriptions

        # Determine whether we want to show values or descriptions
        show_desc = bool(ctx.args)

        # Build the appropriate table
        properties = list(tuser.settings.keys())
        if show_desc:
            values = [tuser.settings[name].desc for name in properties]
        else:
            values = [
                tuser.settings[name]._format_data(
                    ctx.client,
                    ctx.author.id,
                    tuser.settings[name]._data_from_value(ctx.client, ctx.author.id, getattr(tuser, name)),
                )
                for name in properties
            ]
        setting_table = prop_tabulate(properties, values)

        desc: str = f"""{setting_table}
        To see more detailed information use `{await ctx.best_prefix()}typstconfig <option>`.
        To set an option use `{await ctx.best_prefix()}typstconfig <option> <value>`."""

        # Create the preamble field contents
        if show_desc:
            preamble_field: str = f"""Personal persistent compilation preamble, used for defining set rules and imports that may be used across all compilations.
                See `{await ctx.best_prefix()}help typstpreamble` for more information."""
        else:
            if tuser.preamble:
                preamble_field: str = f"Using a personal preamble with `{len(tuser.preamble.splitlines())}` lines!"
            else:
                preamble_field = f"Using the global default preamble (`{len(default_preamble.splitlines())}` lines)."

            preamble_field += f"\nUse `{await ctx.best_prefix()}typstpreamble` to view or modify your preamble!"

        # We have all the components, build the embed and post
        embed = discord.Embed(
            title="Personal Typst configuration.",
            description=desc,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            colour=LuaTeXitCC["yellow"],
        )
        embed.add_field(name="Preamble", value=preamble_field)

        await ctx.reply(embed=embed)
    else:
        # View or set a given option

        # First obtain the option
        splits = ctx.args.split(maxsplit=1)
        option = splits[0].lower()
        valuestr = splits[1] if len(splits) > 1 else None

        # Handle aliases
        if option == "color":
            option = "colour"

        # Retrieve the corresponding setting, if possible
        if option == "preamble":
            return await ctx.error_reply("Use the `typstpreamble` command to view or modify your preamble.")
        if option not in tuser.settings:
            return await ctx.error_reply(
                f"I don't recognise the option `{option}`. Use `{await ctx.best_prefix()}typstconfig` to see the list of options.",
            )
        setting = tuser.settings[option]
        current_value = getattr(tuser, option)

        if not valuestr:
            # View information about the option
            return await ctx.reply(embed=setting.info_embed(ctx, current_value))
        # Set the option
        return await setting.user_set(ctx, valuestr)
    return None
