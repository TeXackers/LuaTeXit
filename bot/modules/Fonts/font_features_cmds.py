import asyncio
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

import discord
from cmdClient import Context  # noqa
from cmdClient.Format import bf, footnote
from fontTools import unicodedata as ot_unicodedata
from fontTools.ttLib import TTFont
from iso639 import Language, LanguageNotFoundError
from utils.lib import tabulate

from .font_cmds import clean_md, run_fc_list, run_fc_match
from .module import fonts_module as module
from .ot_language_tags import OT_LANGUAGE_TAGS

"""
Provides the fontfeatures command.
"""

# Grouped following fontspec's OpenType feature categorisation, used by the `--fontspec` flag.
# "cvXX"/"ssXX" stand in for the numbered character-variant/stylistic-set tags (cv01.. / ss01..).
FEATURE_GROUPS: dict[str, set[str]] = {
    "Character Width": {"pwid", "fwid", "hwid", "twid", "qwid", "palt", "halt"},
    "CJK Shape": {"trad", "smpl", "jp78", "jp83", "jp90", "expt", "nlck"},
    "Contextuals": {"cswh", "cvXX", "calt", "init", "fina", "falt", "medi"},
    "Diacritics": {"mark", "mkmk", "abvm", "blwm"},
    "Fractions": {"frac", "afrc"},
    "Kerning": {"kern", "cpsp"},
    "Letters": {"smcp", "pcap", "c2sc", "c2pc", "unic"},
    "Ligatures": {"rlig", "liga", "clig", "dlig", "hlig", "tlig"},
    "Local Forms": {"locl"},
    "Numbers": {"lnum", "onum", "pnum", "tnum", "zero", "anum"},
    "Style": {"ssXX", "salt", "curs", "hist", "ital", "ruby", "swsh", "titl", "case", "hkna", "vkna"},
    "Vertical Positions": {"sups", "subs", "numr", "dnom", "sinf", "ordn"},
    "Vertical": {"vrt2", "vrtr", "vert", "vkna", "vkrn", "valt", "vhal", "vpal"},
}
OTHER_GROUP = "Other"

TAG_TO_GROUP: dict[str, str] = {
    tag: group for group, tags in FEATURE_GROUPS.items() for tag in tags if not tag.endswith("XX")
}
NUMBERED_GROUP_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(rf"^{tag[:-2]}\d\d$"), group)
    for group, tags in FEATURE_GROUPS.items()
    for tag in tags
    if tag.endswith("XX")
]

# name-table IDs shown in the "Font info" block, `otfinfo -i`-style, in display order.
NAME_ID_COPYRIGHT = 0
# NAME_ID_UNIQUE_ID = 3
NAME_ID_VERSION = 5
NAME_ID_TRADEMARK = 7
NAME_ID_MANUFACTURER = 8
NAME_ID_DESIGNER = 9
NAME_ID_VENDOR_URL = 11
NAME_ID_DESIGNER_URL = 12
NAME_ID_LICENSE = 13
# NAME_ID_LICENSE_URL = 14


def group_for(tag: str) -> str:
    """Resolve a raw OpenType feature tag to its fontspec-style category."""
    if tag in TAG_TO_GROUP:
        return TAG_TO_GROUP[tag]
    for pattern, group in NUMBERED_GROUP_PATTERNS:
        if pattern.match(tag):
            return group
    return OTHER_GROUP


@dataclass
class FontStyle:
    family: str
    style: str
    file: str
    index: int


async def resolve_font_styles(family_query: str) -> list[FontStyle]:
    """
    Look up every installed style for the fontconfig family matching `family_query` exactly (case-insensitively).

    Returns an empty list if no such family is installed.
    """
    out, err = await run_fc_list(f":family={family_query}", "-f", "%{family}|%{style}|%{file}|%{index}\n")
    if err:
        return []

    styles: list[FontStyle] = []
    for line in out.decode("utf-8").splitlines():
        if not line.strip():
            continue
        family, style, file, index = line.split("|", 3)
        styles.append(FontStyle(family=family.split(",")[0], style=style.split(",")[0], file=file, index=int(index)))
    return styles


async def match_regular(family: str) -> FontStyle | None:
    """
    Ask fontconfig for its best "Regular" match within `family`.

    fc-match always returns *something* (falling back to a default font), so the caller must
    already know `family` is installed; the result is discarded unless it actually reports back
    that same family, guarding against a silent fallback.
    """
    out, err = await run_fc_match(f":family={family}:style=Regular", "-f", "%{family}|%{style}|%{file}|%{index}\n")
    if err or not out:
        return None

    line = out.decode("utf-8").splitlines()[0]
    matched_family, style, file, index = line.split("|", 3)
    if family.lower() not in (f.strip().lower() for f in matched_family.split(",")):
        return None
    return FontStyle(family=matched_family.split(",")[0], style=style.split(",")[0], file=file, index=int(index))


async def suggest_families(query: str, limit: int = 8) -> list[str]:
    """Suggest installed family names that contain `query` as a substring, for when the exact lookup misses."""
    out, err = await run_fc_list(":", "family")
    if err:
        return []

    needle = query.lower()
    families = {
        line.split(",")[0].strip()
        for line in out.decode("utf-8").splitlines()
        if line.strip() and not line.startswith(".")
    }
    return sorted(f for f in families if needle in f.lower())[:limit]


def _script_label(tag: str) -> str:
    """Human-readable name for an OpenType script tag, e.g. `arab` -> `Arabic`."""
    if tag.strip() == "DFLT":
        return "Default"
    iso_code = ot_unicodedata.ot_tag_to_script(tag)
    if not iso_code:
        return tag.strip()
    try:
        return ot_unicodedata.script_name(iso_code)
    except KeyError:
        return tag.strip()


def _language_label(tag: str) -> str:
    """Human-readable name for an OpenType language-system tag, e.g. `ARA ` -> `Arabic`."""
    code = OT_LANGUAGE_TAGS.get(tag)
    if not code:
        return tag.strip()
    try:
        return Language.match(code).name
    except LanguageNotFoundError:
        return tag.strip()


def _scripts_supported(font: TTFont) -> list[tuple[str, str]]:
    """
    Every script, and script/language-system combination, declared across GSUB and GPOS.

    Mirrors `otfinfo -s`: one entry per script tag, plus one entry per non-default language
    system registered under that script (`arab.URD` -> `Arabic/Urdu`).
    """
    scripts: dict[str, set[str]] = {}
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        script_list = font[table_tag].table.ScriptList
        if script_list is None:
            continue
        for record in script_list.ScriptRecord:
            langs = scripts.setdefault(record.ScriptTag, set())
            if record.Script.LangSysRecord:
                langs.update(lang_rec.LangSysTag for lang_rec in record.Script.LangSysRecord)

    entries: list[tuple[str, str]] = []
    for script_tag in sorted(scripts):
        script_label = _script_label(script_tag)
        entries.append((script_tag.strip(), script_label))
        entries.extend(
            (f"{script_tag.strip()}.{lang_tag.strip()}", f"{script_label}/{_language_label(lang_tag)}")
            for lang_tag in sorted(scripts[script_tag])
        )
    return entries


def _font_info(font: TTFont) -> dict[str, str]:
    """Name-table and general font info, `otfinfo -i`-style."""
    name = font["name"]

    def debug(name_id: int) -> str | None:
        return name.getDebugName(name_id)

    family, subfamily = debug(1), debug(2)
    pref_family, pref_subfamily = debug(16), debug(17)

    if "CFF2" in font:
        outline = "OpenType/CFF2"
    elif "CFF " in font:
        outline = "OpenType/CFF"
    elif "glyf" in font:
        outline = "TrueType"
    else:
        outline = font.sfntVersion
    if "fvar" in font:
        outline += " (variable)"

    fields: list[tuple[str, str | None]] = [
        ("Family", family),
        ("Subfamily", subfamily),
        ("Preferred family", pref_family if pref_family and pref_family != family else None),
        ("Preferred subfamily", pref_subfamily if pref_subfamily and pref_subfamily != subfamily else None),
        ("Full name", debug(4)),
        ("PostScript name", debug(6)),
        ("Font type", outline),
        ("Units/Em", str(font["head"].unitsPerEm) if "head" in font else None),
        ("Glyphs", str(font["maxp"].numGlyphs) if "maxp" in font else None),
        (
            "Weight/Width",
            f"{font['OS/2'].usWeightClass} / {font['OS/2'].usWidthClass}" if "OS/2" in font else None,
        ),
        ("Version", debug(NAME_ID_VERSION)),
        # ("Unique ID", debug(NAME_ID_UNIQUE_ID)),
        ("Manufacturer", debug(NAME_ID_MANUFACTURER)),
        ("Designer", debug(NAME_ID_DESIGNER)),
        ("Vendor URL", debug(NAME_ID_VENDOR_URL)),
        ("Designer URL", debug(NAME_ID_DESIGNER_URL)),
        ("Licence", debug(NAME_ID_LICENSE)),
        # ("Licence URL", debug(NAME_ID_LICENSE_URL)),
        ("Copyright", debug(NAME_ID_COPYRIGHT)),
        ("Trademark", debug(NAME_ID_TRADEMARK)),
    ]
    return {label: value for label, value in fields if value}


@dataclass
class FontData:
    info: dict[str, str]
    tables: dict[str, list[str]]
    scripts: list[tuple[str, str]]


def _read_font_data(path: str, index: int) -> FontData:
    font = TTFont(path, fontNumber=index, lazy=True)

    tables: dict[str, list[str]] = {}
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        feature_list = font[tag].table.FeatureList
        if feature_list is not None:
            tables[tag] = sorted({record.FeatureTag for record in feature_list.FeatureRecord})

    return FontData(info=_font_info(font), tables=tables, scripts=_scripts_supported(font))


async def read_font_data(path: str, index: int) -> FontData:
    """Parse a font file's info, GSUB/GPOS feature tags, and supported scripts on a worker thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _read_font_data, path, index)


@module.cmd(
    "fontfeatures",
    desc="Looks up information, OpenType features, and scripts supported by a font",
    aliases=["ff"],
    flags=["fontspec", "fs"],
)
async def cmd_fontfeatures(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}fontfeatures <font name> [--fontspec/-fs]
    Description:
        Look up a font installed on LuaTeXit's system.

        Pass `--fontspec`|`-fs` to instead group the features the way `fontspec` groups them.

        Use `{prefix}findfont --name <pattern>` first if you don't know the exact family name.
    Flags::
        fontspec: fs: Group features fontspec-style instead of showing font info/features/scripts.
    Examples``:
        {prefix}fontfeatures Adobe Arabic
        {prefix}ff STIX Two Text --fontspec
    """
    query = clean_md(ctx.args)
    if not query:
        return await ctx.error_reply(await ctx.format_usage())

    t_start = time.monotonic()
    styles = await resolve_font_styles(query)
    if not styles:
        suggestions = await suggest_families(query)
        if suggestions:
            suggestion_text = "\n".join(f"- {bf(discord.utils.escape_mentions(s))}" for s in suggestions)
            return await ctx.error_reply(
                f"No font family found matching {bf(query)} exactly. Did you mean:\n\n{suggestion_text}"
            )
        return await ctx.error_reply(
            f"No font found matching {bf(query)}.\n"
            f"Try `{await ctx.best_prefix()}findfont --name {query}` to search by name."
        )

    canonical_family = styles[0].family
    family = discord.utils.escape_mentions(canonical_family)
    chosen = await match_regular(canonical_family) or styles[0]

    try:
        data = await read_font_data(chosen.file, chosen.index)
    except Exception as e:
        ctx.log(f"Failed to parse font at {chosen.file!r}: {e}", context="fonts", level=logging.ERROR)
        return await ctx.error_reply(f"Could not read the font file for {bf(family)}.")

    all_tags = sorted({tag for tags in data.tables.values() for tag in tags})
    if not all_tags:
        return await ctx.error_reply(f"{bf(family)} ({chosen.style}) has no OpenType layout features.")

    footnote_text = f"{Path(chosen.file).name} · {chosen.style}"

    if flags["fontspec"] or flags["fs"]:
        grouped: dict[str, list[str]] = {}
        for tag in all_tags:
            grouped.setdefault(group_for(tag), []).append(tag)

        lines: list[str] = []
        for group in (*FEATURE_GROUPS.keys(), OTHER_GROUP):
            if group not in grouped:
                continue
            tags_fmt = " ".join(f"`{tag}`" for tag in grouped[group])
            lines.append(f"**{group}**\n{tags_fmt}")

        title_text = f"OpenType features (fontspec-grouped): {family}\n{footnote(footnote_text)}"
        ctx.log(f"fontfeatures finished in {time.monotonic() - t_start:.3f}s.", context="fonts", level=logging.DEBUG)
        return await ctx.pager_v2(content=lines, title=title_text, code=False, maxheight=25)

    features_text = " ".join(f"`{tag}`" for tag in all_tags)
    tag_length = max(len(tag) for tag, label in data.scripts)
    scripts_text = (
        "\n".join(f"`{tag:<{tag_length}}` {label}" for tag, label in data.scripts) if data.scripts else "None declared"
    )

    lines = [
        "**Font info**",
        tabulate(data.info),
        "",
        "**OpenType features**",
        features_text,
        "",
        "**Scripts supported**",
        scripts_text,
    ]

    title_text = f"Font info: {family}\n{footnote(footnote_text)}"
    ctx.log(f"fontfeatures finished in {time.monotonic() - t_start:.3f}s.", context="fonts", level=logging.DEBUG)
    return await ctx.pager_v2(content=lines, title=title_text, code=False, maxheight=30)
