from typing import ClassVar, override

import discord
from cmdClient import Context, cmdClient
from constants import LuaTeXitCC
from settings import BadUserInput, Boolean, Integer, IntegerEnum, SettingType, String
from utils.lib import prop_tabulate, tabulate

from .tex_utils import AutoTexLevel, TexNameStyle


class LatexUserSetting(SettingType):
    """
    Abstract base class for a `LatexUser` setting.
    Intended to hold the logic for conversion between the following setting representations,
    and additionally storing the data.

    data:
        The setting data as stored in the database.
    value:
        The setting value, as used in the application.
    userstr:
        The user-input which possibly represents setting information.
    formatted_data:
        The setting information in a human readable form, accounting for context.

    Uses the `SettingType` abstract mixin interface.
    """

    # The human-readable name of the setting
    name: str | None = None

    # The default setting value
    default = None

    # The message to send on parsing failure (i.e. BadUserInput)
    _parsing_failed_response: str | None = None

    # The data column name
    _data_column: str | None = None

    # The upsert constraint
    _upsert_constraint = "userid"

    # Other user-data caches to refresh when a setting on this table changes (in addition to `LatexUser`)
    _linked_user_caches: ClassVar[list] = []

    @classmethod
    def save(cls, client, userid, data):
        """
        Uses the appropriate tableInterface to save the data, then refreshes the cached `LatexUser` (and any linked user caches, see `_linked_user_caches`) so as to not serve stale settings.
        """
        params = {"userid": userid, cls._data_column: data}

        client.data.user_latex_config.upsert(constraint=cls._upsert_constraint, **params)

        # Imported lazily to avoid a circular import: `LatexUser` imports this module.
        from .LatexUser import LatexUser  # noqa

        if userid in LatexUser.cached_users:
            LatexUser.cached_users[userid].load()

        for other_cache_cls in cls._linked_user_caches:
            if userid in other_cache_cls.cached_users:
                other_cache_cls.cached_users[userid].load()

    @classmethod
    def response(cls, ctx, new_data):
        """
        Generate the appropriate response, possibly dynamically, after successfuly setting the property.
        """
        raise NotImplementedError

    @classmethod
    def info_embed(cls, ctx, current_data):
        """
        A detailed embed for the setting.
        Must be provided the current data value.
        """
        embed = discord.Embed(title=f"Configuration options for `{cls.name}`", color=LuaTeXitCC["purple"])
        fields = ("Current value", "Default value", "Accepted input")
        values = (
            cls._format_data(ctx.client, ctx.author.id, current_data),
            cls._format_data(ctx.client, ctx.author.id, cls.default) or "None",
            cls.accepts,
        )
        table = prop_tabulate(fields, values)
        embed.description = f"{cls.desc}\n{table}"
        return embed

    @classmethod
    async def user_set(cls, ctx, userstr):
        """
        Set a user setting given a message context, handling parsing, saving, and responses.
        """
        user = ctx.author
        try:
            data = await cls._parse_userstr(ctx, user.id, userstr)
        except BadUserInput as e:
            response = cls._parsing_failed_response or "{error.msg}\n"

            desc = response.format(ctx=ctx, userstr=userstr, prefix=ctx.best_prefix(), cls=cls, error=e)

            embed = discord.Embed(title="Couldn't parse your input!", description=desc, color=discord.Color.red())
            embed.set_footer(
                text=f"Use `{await ctx.best_prefix()}texconfig {cls.name}` to see more detailed information about this setting.",
            )

            return await ctx.reply(embed=embed)

        cls.save(ctx.client, user.id, data)
        response = cls.response(ctx, data)
        return await ctx.reply(response)


class autotex(LatexUserSetting, Boolean):
    name = "autotex"
    desc = "Whether to automatically compile LaTeX in your messages."

    default = False
    _outputs: ClassVar[dict[bool, str]] = {
        True: "Enabled (may be restricted by guild settings)",
        False: "Disabled (may be overriden by guild settings)",
    }

    _parsing_failed_response = "Unknown option `{userstr}`.\nPlease use `on` or `off`."

    _data_column = "autotex"

    @classmethod
    def response(cls, ctx: Context, data):
        match data:
            case True:
                return (
                    "I will now listen for and compile LaTeX in your messages! "
                    "Be aware that automatic compilation may be "
                    "restricted by other guild and personal settings."
                )
            case False:
                return (
                    "You have disabled personal automatic compilation! "
                    "Messages will still be automatically compiled "
                    "in guilds with the `latex` setting enabled."
                )
            case None:
                return "Unset `autotex`!"


class keepsourcefor(LatexUserSetting, Integer):
    name = "keepsourcefor"
    desc = "How many seconds to keep source for after compilation ('None' to never delete)."
    accepts = "A non-negative number of seconds, or `None` to keep forever."

    default = None
    _min = 0
    _parsing_failed_response = "{error.msg}"

    _data_column = "keepsourcefor"

    @classmethod
    def _format_data(cls, client, userid, data, **kwargs):
        """
        Add some decoration to the number, and handle the default.
        """
        if data is None:
            return "Don't delete source (may be overriden by the guild)"
        return f"`{data}` seconds"

    @classmethod
    def response(cls, ctx, data):
        if data is None:
            return "No longer automatically deleting your LaTeX source."
        return f"Your source will be deleted {data} seconds after a succesful compilation (if not edited)."


class colour(LatexUserSetting, String):
    desc = "Your colourscheme."
    name = "colour"
    accepts = "One of the colourschemes listed below."

    colourschemes: ClassVar[dict[str, str]] = {
        "white": "Pure white background, with black text.",
        "light": "Very light grey background, with black text.",
        "ash": "Discord's `ash` background, with white text.",
        "dark": "Discord's `dark` background with white text.",
        "onyx": "Discord's `onyx` background, with white text.",
        "transparent": "Transparent background, with white text.",
        "trans_black": "Transparent background, with black text.",
    }
    tabled_colourschemes = tabulate(colourschemes)

    default = "white"
    _options = set(colourschemes.keys()) | {"grey", "gray", "trans_white", "darkgrey", "darkgray", "black", "default"}
    _parsing_failed_response = f"Unknown colourscheme `{{userstr}}`. Valid colourschemes:\n{tabled_colourschemes}"

    _data_column = "colour"

    @classmethod
    def _format_data(cls, client, userid, data, **kwargs):
        """
        Add some decoration to the number, and handle the default.
        """
        if data is None:
            return "Using the default colourscheme"
        return f"Using the `{data}` colourscheme"

    @classmethod
    def info_embed(cls, ctx, data):
        embed = super().info_embed(ctx, data)
        embed.add_field(name="Colourschemes", value=cls.tabled_colourschemes)
        return embed

    @classmethod
    def response(cls, ctx, data):
        if data is None:
            return "You are now using the default colourscheme."
        return f"You have switched to the `{data}` colourscheme."


class alwaysmath(LatexUserSetting, Boolean):
    name = "alwaysmath"
    desc = "Whether to always use mathmode with the `tex` command."

    default = False
    _outputs: ClassVar[dict[bool, str]] = {True: "Enabled", False: "Disabled"}
    _parsing_failed_response = "Unknown option `{userstr}`.\nPlease use `on` or `off`."

    _data_column = "alwaysmath"

    @classmethod
    def response(cls, ctx, data):
        if not data:
            return "The `tex` command will now render in text mode. (default)"
        return "The `tex` command will now render in maths mode, i.e., in a `gather*` environment."


class alwayswide(LatexUserSetting, Boolean):
    name = "alwayswide"
    desc = "Whether to skip the automatic horizontal addition of transparent pixels to LaTeX output."

    default = False
    _outputs: ClassVar[dict[bool, str]] = {True: "Enabled", False: "Disabled"}
    _parsing_failed_response = "Unknown option `{userstr}`.\nPlease use `on` or `off`."

    _data_column = "alwayswide"

    @classmethod
    def response(cls, ctx, data):
        if not data:
            return (
                "Transparent pixels will be added to your rendered LaTeX to improve previews.\n"
                "Use the `texw` command to disable this for a single compile."
            )
        return (
            "Transparent pixels will no longer be added to your rendered LaTeX.\n"
            ":warning: If your input is short, Discord will make the rendered image huge!"
        )


class namestyle(LatexUserSetting, IntegerEnum):
    name = "namestyle"
    desc = "The type of name to display with your LaTeX output."
    accepts = "One of the types listed below."
    namestyles: ClassVar[dict[str, str]] = {
        "USERNAME": "Your global username. (**{ctx.author.name}**)",
        "NICKNAME": "Your server nickname. (**{ctx.author.display_name}**)",
        "MENTION": "A mention. {ctx.author.mention}",
        "HIDDEN": "No name.",
    }

    default = TexNameStyle.NICKNAME.value
    _enum = TexNameStyle
    _parsing_failed_response = f"Unknown namestyle `{{userstr}}`. Valid namestyles:\n{tabulate(namestyles)}"

    _data_column = "namestyle"

    @classmethod
    def response(cls, ctx: Context, data) -> str:
        match data:
            case None:
                return "Your namestyle has been returned to the default."
            case TexNameStyle.USERNAME.value:
                return "Your username will now be shown on your LaTeX output."
            case TexNameStyle.NICKNAME.value:
                return "Your guild nickname, if set, will now be shown on your LaTeX output."
            case TexNameStyle.MENTION.value:
                return "You will now be mentioned with your LaTeX output."
            case TexNameStyle.HIDDEN.value:
                return (
                    "Your name will no longer be shown on LaTeX output.\n"
                    "Note that the name of the output image is your userid, so you are still identifiable."
                )

    @classmethod
    def info_embed(cls, ctx: Context, data):
        embed = super().info_embed(ctx, data)
        props = cls.namestyles.keys()
        values = [val.format(ctx=ctx) for val in cls.namestyles.values()]
        embed.add_field(name="Name styles", value=tabulate(dict(zip(props, values, strict=True))))
        return embed


class autotex_level(LatexUserSetting, IntegerEnum):
    name = "autotex_level"
    desc = "How strict the parser is when looking for LaTeX in your messages."
    accepts = "One of the levels listed below."

    tex_levels: ClassVar[dict[str, str]] = {
        "CODEBLOCK": r"The strictest level, require a `tex` or `latex` syntax codeblock.",
        "STRICT": r"Also recognise environments, `$$...$$`, `\(...\)` and `\[...\]`.",
        "WEAK": r"Also recognise paired single dollars, i.e. `$...$`, but not `\$...\$`",
    }
    tabled_levels = tabulate(tex_levels)

    default = AutoTexLevel.WEAK
    _enum = AutoTexLevel
    _parsing_failed_response = f"Unknown autotex level `{{userstr}}`. Valid levels:\n{tabled_levels}"

    _data_column = "autotex_level"

    @classmethod
    def response(cls, ctx: Context, data) -> str:
        match data:
            case None:
                return "Your autotex level has been returned to the default."
            case AutoTexLevel.CODEBLOCK:
                return "I will now only render your messages with `tex` or `latex` codeblocks."
            case AutoTexLevel.STRICT:
                return (
                    "I will now require explicit mathmode macros, environments or codeblocks to render your messages.\n"
                    "Guild configuration (`latex_level`) may locally upgrade this to `CODEBLOCK`."
                )
            case AutoTexLevel.WEAK:
                return (
                    "I will now do my best to detect all LaTeX in your messages.\n"
                    "Guild configuration (`latex_level`) may locally upgrade this to `STRICT` or `CODEBLOCK`."
                )

    @classmethod
    def info_embed(cls, ctx: Context, data) -> type[discord.Embed]:
        embed = super().info_embed(ctx, data)
        embed.add_field(name="LaTeX Levels", value=cls.tabled_levels)
        return embed
