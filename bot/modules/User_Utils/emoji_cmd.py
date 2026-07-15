import re
from typing import TYPE_CHECKING

import discord
from cmdClient import Context  # noqa
from cmdClient.Layouts import GenericFullEmbed
from constants import LuaTeXitCC
from utils.lib import tabulate

from .emojis import emoji_names_by_unicode, emojis_by_name
from .module import utils_module as module

if TYPE_CHECKING:
    from discord.emoji import Emoji

default_emoji_url = "https://jdecked.github.io/twemoji/v/latest/72x72/{}.png"


def get_custom_emoji(ctx: Context, emoji_str: str):
    # Not valid emoji name or emoji id
    # Cross fingers and hope it is of form a:name:id, <a:name:id>, name:id, or <:name:id>
    # Give up otherwise
    if not re.match(r"^[A-Za-z0-9_]+$", emoji_str):
        emoji_id = re.search(r"\d+", emoji_str)
        if not emoji_id:
            return None
        emoji_id = int(emoji_id.group())
        return discord.utils.get(ctx.client.emojis, id=emoji_id)

    # Not valid emoji id
    # Priority: guild exact match > guild inexact match > exact match > inexact match
    if not emoji_str.isdigit():
        if ctx.guild:
            return (
                discord.utils.find(lambda e: emoji_str.lower() == e.name.lower(), ctx.guild.emojis)
                or discord.utils.find(lambda e: emoji_str.lower() in e.name.lower(), ctx.guild.emojis)
                or discord.utils.find(lambda e: emoji_str.lower() == e.name.lower(), ctx.client.emojis)
                or discord.utils.find(lambda e: emoji_str.lower() in e.name.lower(), ctx.client.emojis)
            )
        return discord.utils.find(
            lambda e: emoji_str.lower() == e.name.lower(),
            ctx.client.emojis,
        ) or discord.utils.find(lambda e: emoji_str.lower() in e.name.lower(), ctx.client.emojis)

    # Valid emoji id
    if ctx.guild:
        return discord.utils.get(ctx.guild.emojis, id=int(emoji_str)) or discord.utils.get(
            ctx.client.emojis,
            id=int(emoji_str),
        )
    return discord.utils.get(ctx.client.emojis, id=int(emoji_str))


def unicode_char_rep(uni: str) -> str:
    # 65039 is fe0f, doesn't play nicely with Twemoji
    return "-".join(f"{ord(c):X}".lower() for c in uni if ord(c) >= 128 and ord(c) != 65039)


def search_emojis(emojis: list[Emoji], query: str) -> list[Emoji]:
    exact = [e for e in emojis if query == e.name.lower() or query == str(e.id)]
    if exact:
        return exact
    return [e for e in emojis if query in e.name.lower()]


def unicode_key(uni: str) -> str:
    # Matches the (unfiltered) hex-codepoint key format used by emoji_names_by_unicode,
    # unlike unicode_char_rep which strips FE0F for Twemoji's URL scheme.
    return "-".join(f"{ord(c):x}" for c in uni)


def search_unicode_emojis(query: str) -> list[str]:
    # Query may itself be a pasted unicode emoji; look up its name directly first
    reverse_name = emoji_names_by_unicode.get(unicode_key(query))
    if reverse_name:
        return [reverse_name]

    if query in emojis_by_name:
        return [query]

    return [name for name in emojis_by_name if query in name]


def build_emoji_embed(emoji: Emoji, source: str) -> GenericFullEmbed:
    return GenericFullEmbed(
        header=emoji.name,
        body=tabulate(
            {
                "ID": f"`{emoji.id}`",
                "Animated": "Yes" if emoji.animated else "No",
                "Managed": "Yes" if emoji.managed else "No",
                "Source": source,
            },
        ),
        footer=f"Usage: `{emoji}`",
        thumbnail_url=emoji.url,
        accent_colour=LuaTeXitCC["yellow"],
    )


@module.cmd(
    "emoji",
    desc="Displays/searches info about the app's emojis",
    aliases=["e"],
    flags=["guild", "server", "g", "s"],
)
async def cmd_emoji(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}emoji [<query>] [-guild|-server|-g|-s]
    Description:
        Displays the application's custom emojis.
        If a query is given, searches for it amongst the application's emojis,
        this guild's emojis, and the known unicode emojis, by name or ID.
    Flags::
        guild|server|g|s: Restrict everything to this guild's own emojis.
    Examples``:
        {prefix}e catThink
        {prefix}e -g catThink
    """
    query = ctx.args.strip().lower() if ctx.args else ""

    # -guild/-server/-g/-s restricts the whole command to this guild's own emojis
    if flags["guild"] or flags["server"] or flags["g"] or flags["s"]:
        if not ctx.guild:
            return await ctx.error_reply("This flag can only be used within a guild.")

        guild_emojis: list[Emoji] = list(ctx.guild.emojis)

        if not query:
            if not guild_emojis:
                return await ctx.error_reply("This guild has no emojis.")

            lines = [f"{i}. {emoji} `{emoji.name}`" for i, emoji in enumerate(guild_emojis, start=1)]
            return await ctx.pager_v2("\n".join(lines), title=f"Guild emojis ({len(guild_emojis)})")

        guild_matches = search_emojis(guild_emojis, query)
        if not guild_matches:
            return await ctx.error_reply(f"No guild emoji found matching `{ctx.args}`.")

        if len(guild_matches) == 1:
            return await ctx.reply(view=build_emoji_embed(guild_matches[0], "Guild"))

        lines = [f"{i}. {emoji} `{emoji.name}`" for i, emoji in enumerate(guild_matches, start=1)]
        return await ctx.pager_v2("\n".join(lines), title=f"Guild emoji search results for `{ctx.args}`")

    # fetch app emojis
    app_emojis: list[Emoji] = await ctx.client.fetch_application_emojis()

    # no query = show all app emojis instead
    if not query:
        if not app_emojis:
            return await ctx.error_reply("This app has no emojis.")

        lines = [f"{i}. {emoji} `{emoji.name}`" for i, emoji in enumerate(app_emojis, start=1)]
        return await ctx.pager_v2("\n".join(lines), title=f"Application emojis ({len(app_emojis)})")

    # if query, try to find the emoji by name or id
    # here, we look for application emojis, this guild's emojis, and unicode emojis
    # see emojis.py for the unicode emoji database
    guild_emojis = list(ctx.guild.emojis) if ctx.guild else []

    app_matches = search_emojis(app_emojis, query)
    guild_matches = search_emojis(guild_emojis, query)
    unicode_matches = search_unicode_emojis(query)

    if not app_matches and not guild_matches and not unicode_matches:
        return await ctx.error_reply(f"No application, guild, or unicode emoji found matching `{ctx.args}`.")

    # Single unambiguous match, show it in full
    if len(app_matches) + len(guild_matches) + len(unicode_matches) == 1:
        if app_matches or guild_matches:
            emoji, source = (app_matches[0], "Application") if app_matches else (guild_matches[0], "Guild")
            return await ctx.reply(view=build_emoji_embed(emoji, source))

        name = unicode_matches[0]
        char = emojis_by_name[name]
        return await ctx.reply(
            view=GenericFullEmbed(
                header=name,
                body=tabulate({"Character": char, "Source": "Unicode"}),
                footer="Unicode emoji",
                thumbnail_url=default_emoji_url.format(unicode_char_rep(char)),
                accent_colour=LuaTeXitCC["yellow"],
            ),
        )

    # Multiple matches
    lines = [f"{i}. {emoji} `{emoji.name}` (Application)" for i, emoji in enumerate(app_matches, start=1)]
    lines += [
        f"{i}. {emoji} `{emoji.name}` (Guild)" for i, emoji in enumerate(guild_matches, start=len(app_matches) + 1)
    ]
    lines += [
        f"{i}. {emojis_by_name[name]} `{name}` (Unicode)"
        for i, name in enumerate(unicode_matches, start=len(app_matches) + len(guild_matches) + 1)
    ]
    return await ctx.pager_v2("\n".join(lines), title=f"Emoji search results for `{ctx.args}`")
