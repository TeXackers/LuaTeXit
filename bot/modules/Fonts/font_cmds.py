import asyncio
import logging
import os
import re
import time
from asyncio.subprocess import PIPE
from dataclasses import dataclass

import discord
from cmdClient import Context
from cmdClient.Format import bf, footnote
from iso639 import Language, LanguageNotFoundError
from utils.cache import async_ttl_cache
from utils.interactive import get_application_emoji_by_name

from modules.Typst.resources import extra_font_paths

from .module import fonts_module as module
from .resources import fontconfig_file

"""
Provides the findfont command.
"""

fontconfig_env = {**os.environ, "FONTCONFIG_FILE": str(fontconfig_file)}


@async_ttl_cache(days=7)
async def run_fc_list(*args: str) -> tuple[bytes, bytes]:
    """Run `fc-list <args>`, caching the result since installed fonts rarely change."""
    proc = await asyncio.create_subprocess_exec("fc-list", *args, stdout=PIPE, stderr=PIPE, env=fontconfig_env)
    return await proc.communicate()


@async_ttl_cache(days=7)
async def run_typst_fonts() -> tuple[bytes, bytes]:
    """
    Run `typst fonts` for caching purposes.

    Excludes fonts embedded in the `typst` binary itself.
    """
    proc = await asyncio.create_subprocess_exec(
        "typst",
        "fonts",
        "--ignore-embedded-fonts",
        "--font-path",
        extra_font_paths,
        stdout=PIPE,
        stderr=PIPE,
    )
    return await proc.communicate()


@async_ttl_cache(days=7)
async def run_fc_match(*args: str) -> tuple[bytes, bytes]:
    """Run `fc-match <args>` for caching purposes."""
    proc = await asyncio.create_subprocess_exec("fc-match", *args, stdout=PIPE, stderr=PIPE, env=fontconfig_env)
    return await proc.communicate()


async def regex_filter(pattern: re.Pattern, items: list[str], timeout: float = 2.0) -> list[str] | None:
    """
    Filter `items` by `pattern` on a worker thread.

    Returns
    =======
    None if filtering doesn't finish within `timeout` seconds.
    """
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, lambda: [item for item in items if pattern.search(item)]),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return None


def glyph_or_unicode(arg: str) -> list[str] | None:
    """
    Purpose: Making four or five digit to be used in `:charset` for fc-list.

    Parse the input and determine if it is a unicode or a glyph.
    If it's a glyph, then convert it to its unicode hex value.
    The final output is a string containing a four (preferred) or five-letter unicode hex value.
    Remove any U+ as fontconfig doesn't need it.
    """
    if not arg:
        raise ValueError("Argument cannot be empty.")

    # if space or comma in arg, split it
    if "," in arg:
        argstack: list[str] = arg.split(",")
    else:
        argstack: list[str] = [arg]
    output: list[str] = []

    for a in argstack:
        a = a.strip().lower().lstrip("u+")

        # User enters glyph(s)
        if len(a) == 1:
            # It's a glyph
            output.append(f"{ord(a):05x}")

        # User enters unicode(s)
        elif len(a) > 1:
            a_test = f"{a:0>5}"
            # Is it unicode? Each letter must be between 0-9 or a-f
            if all(c in "0123456789abcdef" for c in a_test):
                # also ensure that the hex value is no greater than 1FA6D
                if int(a_test, 16) <= 0x1FA6D:
                    output.append(a_test)
                else:
                    pass
            else:
                pass
        else:
            pass

    return [o for o in output if o is not None]


def clean_md(text: str) -> str:
    """
    Cleans up markdown text by removing unnecessary whitespace and formatting.
    """
    if not text:
        return ""
    # remove all markdown formatting things, i.e. <>!@#$%^&*()_+-=~`[]{}|;:'",.<>?/
    text = re.sub(r"[<>!@#$%^&*()_+\-=\~`[\]{}|;:'\",.<>?/]", "", text)
    # remove all whitespace characters, i.e. \n, \r, \t, space
    text = re.sub(r"[\n\r\t ]+", " ", text)
    return text.strip()


@dataclass
class SearchParams:
    query: str | None = None
    search_type: str | None = None


@module.cmd(
    "findfont",
    desc="Looks for fonts supporting a given argument",
    aliases=["fc"],
    flags=["char==", "lang==", "name=="],
)
async def cmd_findfont(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}findfont <feature>
    Description:
        Search for fonts in LuaTeXit's system for a given feature or features.

        N.B. `--char` and `--lang` use `fontconfig`, while `--name` and no flags use `typst fonts`.
    Examples``:
        {prefix}findfont --lang <iso639 | name>
        {prefix}findfont --char <unicode hex code | glyph(s)>
        {prefix}findfont --name <regex pattern>
    """
    t_start = time.monotonic()
    fclist_chars: str = ""
    fclist_lang: str = ""
    params = SearchParams()

    if flags["char"]:
        cleaned_chars = ",".join(clean_md(part) for part in flags["char"].split(","))
        requested_chars = glyph_or_unicode(cleaned_chars)
        if not requested_chars:
            return await ctx.reply("Invalid unicode or glyph(s).")
        if len(requested_chars) > 1:
            fclist_chars = ":charset=" + ",".join(requested_chars)
        elif len(requested_chars) == 1:
            fclist_chars = ":charset=" + str(requested_chars[0])
        else:
            ctx.log(f"Requested characters: {requested_chars}", context="fonts", context_level=logging.DEBUG)
            return await ctx.error_reply("Something went wrong while processing the characters.")

        params.query = cleaned_chars
        params.search_type = "character" if len(requested_chars) == 1 else "characters"

    if flags["lang"]:
        requested_language: Language
        if len(flags["lang"]) > 3:
            try:
                requested_language = Language.match(clean_md(flags["lang"]).capitalize())
            except LanguageNotFoundError as e:
                return await ctx.error_reply(f"{e}")
        else:
            try:
                requested_language = Language.match(clean_md(flags["lang"]).lower())
            except LanguageNotFoundError as e:
                return await ctx.error_reply(f"{e}")

        params.query = requested_language.name
        params.search_type = "language"

        fclist_lang: str = ":lang=" + str(requested_language.part1 or requested_language.part2t)

    if flags["char"] or flags["lang"]:
        # fontconfig-backed search: preserves fontspec-compatible names for LaTeX
        t_query = time.monotonic()
        fc_out, fc_err = await run_fc_list(f"{fclist_chars}{fclist_lang}", ":", "family")
        ctx.log(f"fc-list responded in {time.monotonic() - t_query:.3f}s.", context="fonts", level=logging.DEBUG)

        # Error out early
        if fc_err:
            return await ctx.error_reply(f"{fc_err.decode('utf-8')}")

        fc_out = fc_out.decode("utf-8").split("\n")

        if not fc_out:
            return await ctx.reply("No fonts found.")

        # Remove fonts that start with `.`
        fonts = [line.replace("\\", "") for line in fc_out if not line.startswith(".")]
        # Split by `,` and only grab the first element
        fonts = [line.split(",")[0].strip() for line in fonts]

        if flags["name"]:
            params.query = clean_md(flags["name"])
            params.search_type = "name"
            fonts = [f.title() for f in [f.lower() for f in fonts] if clean_md(flags["name"]).lower() in f]
            if not fonts:
                return await ctx.reply(f"No fonts found matching the name:\n\n{bf(clean_md(flags['name']))}.")
    else:
        # Typst-backed search: reports the family names Typst itself recognises
        t_query = time.monotonic()
        typst_out, typst_err = await run_typst_fonts()
        ctx.log(f"typst fonts responded in {time.monotonic() - t_query:.3f}s.", context="fonts", level=logging.DEBUG)

        if typst_err:
            return await ctx.error_reply(f"{typst_err.decode('utf-8')}")

        fonts = [line.strip() for line in typst_out.decode("utf-8").split("\n") if line.strip()]

        if not fonts:
            return await ctx.reply("No fonts found.")

        if flags["name"]:
            raw_pattern = flags["name"].strip()
            # Escape for display only
            display_pattern = discord.utils.escape_mentions(discord.utils.escape_markdown(raw_pattern))
            params.query = display_pattern
            params.search_type = "name"

            try:
                name_re = re.compile(raw_pattern, re.IGNORECASE)
            except re.error:
                return await ctx.reply(f"Invalid regular expression:\n\n{bf(display_pattern)}.")

            matched = await regex_filter(name_re, fonts)
            if matched is None:
                return await ctx.reply("That pattern took too long to evaluate. Try something simpler.")
            fonts = matched
            if not fonts:
                return await ctx.reply(f"No fonts found matching the pattern:\n\n{bf(display_pattern)}.")

    fc_out_sorted: list[str] = sorted(set(fonts))
    fc_out: list[str] = [f for f in fc_out_sorted if f]
    footnote_text = (
        f"searching for {bf(params.query)} by {bf(params.search_type)}"
        if params.query and params.search_type
        else "Showing all fonts"
    )
    title_text = (
        f"Font query ({len(fc_out)} results)\n{footnote(footnote_text)}"
        if flags
        else f"Font query ({len(fc_out)} results)"
    )

    ctx.log(f"findfont finished in {time.monotonic() - t_start:.3f}s.", context="fonts", level=logging.DEBUG)
    return await ctx.pager_v2(content=fc_out, title=title_text, code=True, maxheight=25)
