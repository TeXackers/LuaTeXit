import asyncio
import logging
import re
import time
from dataclasses import dataclass
from enum import IntEnum
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

# Supported/Unsupported OT feature tags (and their equivalent fontspec key-values)
FEATURE_GROUPS: dict[str, dict[str, str] | list[str]] = {
    "Annotation": {
        "nalt": "On/Off",
    },
    "CharacterWidth": {
        "pwid": "Proportional",
        "fwid": "Full",
        "hwid": "Half",
        "twid": "Third",
        "qwid": "Quarter",
        "palt": "AlternateProportional",
        "halt": "AlternateHalf",
    },
    "CJKShape": {
        "trad": "Traditional",
        "smpl": "Simplified",
        "jp78": "JIS1978",
        "jp83": "JIS1983",
        "jp90": "JIS1990",
        "expt": "Expert",
        "nlck": "NLC",
    },
    "Contextuals": {
        "cswh": "Swash",
        "calt": "Alternate",
        "init": "WordInitial",
        "fina": "WordFinal",
        "falt": "LineFinal",
        "medi": "Inner",
    },
    "CharacterVariants": {
        "cvXX": "Character Variant",
    },
    "Diacritics": {
        "mark": "MarkToBase",
        "mkmk": "MarkToMark",
        "abvm": "AboveBase",
        "blwm": "BelowBase",
    },
    "Fractions": {"frac": "On/Off", "afrc": "Alternate"},
    "Kerning": {"kern": "On/Off", "cpsp": "Uppercase"},
    "Letters": {
        "smcp": "SmallCaps",
        "pcap": "PetiteCaps",
        "c2sc": "UppercaseSmallCaps",
        "c2pc": "UppercasePetiteCaps",
        "unic": "Unicase",
    },
    "Ligatures": {
        "rlig": "Required",
        "liga": "Common",
        "clig": "Contextual",
        "dlig": "Rare/Discretionary",
        "hlig": "Historic",
        "tlig": "TeX",
    },
    "LocalForms": {
        "locl": "On/Off",
    },
    "Numbers": {
        "lnum": "Lining",
        "onum": "OldStyle",
        "pnum": "Proportional",
        "tnum": "Tabular",
        "zero": "SlashedZero",
        "anum": "Arabic",
    },
    "Ornaments": {
        "ornm": "On/Off",
    },
    "Style": {
        "salt": "Alternate",
        "curs": "Cursive",
        "hist": "Historic",
        "ital": "Italic",
        "ruby": "Ruby",
        "swsh": "Swash",
        "titl": "Titling",
        "case": "Case",
        "hkna": "HorizontalKana",
        "pkna": "ProportionalKana",
        "vkna": "VerticalKana",
    },
    "StylisticSet": {
        "ssXX": "",
    },
    "VerticalPosition": {
        "sups": "Superier",
        "subs": "Inferior",
        "numr": "Numerator",
        "dnom": "Denominator",
        "sinf": "ScientificInferior",
        "ordn": "Ordinal",
    },
    "Vertical": {
        "vrt2": "RotatedGlyphs",
        "vrtr": "AlternatesForRotation",
        "vert": "Alternates",
        "vkna": "KanaAlternates",
        "vkrn": "Kerning",
        "valt": "AlternateMetrics",
        "vhal": "HalfMetrics",
        "vpal": "ProportionalMetrics",
    },
    "Unsupported": [
        "aalt",
        "abvf",
        "abvs",
        "akhn",
        "blwf",
        "blws",
        "ccmp",
        "cfar",
        "cjct",
        "cpct",
        # "curs",  # also apparently in Style but also in Unsupported...
        "dist",
        "dtls",
        "fin2",
        "fin3",
        "flac",
        "half",
        "haln",
        "hngl",
        "hojo",
        "isol",
        "jalt",
        "lfbd",
        "ljmo",
        "ltra",
        "ltrm",
        "med2",
        "mgrk",
        "mset",
        "nukt",
        "opbd",
        "pref",
        "pres",
        "pstf",
        "psts",
        "rclt",
        "rkrf",
        "rphf",
        "rtbd",
        "rtla",
        "rtlm",
        "rvrn",
        "size",
        "stch",
        "tjmo",
        "tnam",
        "vatu",
        "vjmo",
    ],
}
OTHER_GROUP = "Other"
NUMBERED_GROUPS = {"CharacterVariants", "StylisticSet"}  # these show up as just numbers
CV_TAG_RE = re.compile(r"^cv\d\d$")

TAG_TO_GROUP: dict[str, str] = {
    tag: group for group, tags in FEATURE_GROUPS.items() for tag in tags if not tag.endswith("XX")
}
# OpenType tag to fontspec value name
TAG_TO_VALUE: dict[str, str] = {
    tag: value
    for _, tags in FEATURE_GROUPS.items()
    if isinstance(tags, dict)
    for tag, value in tags.items()
    if not tag.endswith("XX")
}
NUMBERED_GROUP_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(rf"^{tag[:-2]}\d\d$"), group)
    for group, tags in FEATURE_GROUPS.items()
    for tag in tags
    if tag.endswith("XX")
]


class NameID(IntEnum):
    """OpenType name table ID registry."""

    COPYRIGHT = 0
    FAMILY = 1
    SUBFAMILY = 2
    UNIQUE_ID = 3
    FULL_NAME = 4
    VERSION = 5
    POSTSCRIPT_NAME = 6
    TRADEMARK = 7
    MANUFACTURER = 8
    DESIGNER = 9
    DESCRIPTION = 10
    VENDOR_URL = 11
    DESIGNER_URL = 12
    LICENSE = 13
    LICENSE_URL = 14
    # 15 reserved
    PREFERRED_FAMILY = 16
    PREFERRED_SUBFAMILY = 17
    COMPATIBLE_FULL = 18
    SAMPLE_TEXT = 19
    POSTSCRIPT_CID_FINDFONT_NAME = 20
    WWS_FAMILY = 21
    WWS_SUBFAMILY = 22
    LIGHT_BACKGROUND_PALETTE = 23
    DARK_BACKGROUND_PALETTE = 24
    VARIATIONS_PS_NAME_PREFIX = 25


def group_for(tag: str) -> str:
    """Resolve raw OpenType feature tag to its fontspec-style category."""
    if tag in TAG_TO_GROUP:
        return TAG_TO_GROUP[tag]
    for pattern, group in NUMBERED_GROUP_PATTERNS:
        if pattern.match(tag):
            return group
    return OTHER_GROUP


def display_values(
    tag: str,
    group: str,
    cv_variations: dict[str, int] | None = None,
    annotation_counts: list[int] | None = None,
) -> list[str]:
    """
    The string(s) to show for `tag` under its fontspec-style `group` heading.

    - cvXX/ssXX show numbers
    - cvXX with more than one named value shows as `N:count` (e.g. `1:2`)
    - `nalt` expands to every distinct alternate-count it offers
    - Unsupported/uncategorised tags show their OpenType name
    """
    if tag == "nalt":
        return [str(count) for count in annotation_counts] if annotation_counts else [TAG_TO_VALUE.get(tag, tag)]
    if group in NUMBERED_GROUPS:
        number = int(tag[-2:])
        count = (cv_variations or {}).get(tag, 0)
        if group == "CharacterVariants" and count > 1:
            return [f"{number}:{count}"]
        return [str(number)]
    return [TAG_TO_VALUE.get(tag, tag)]


@dataclass
class FontStyle:
    family: str
    style: str
    file: str
    index: int


async def resolve_font_styles(family_query: str) -> list[FontStyle]:
    """
    Look up every installed style for the fontconfig family.

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

    `fc-match` always returns *something* (falling back to a default font), so the caller must
    already know `family` is installed. the result is discarded unless it actually reports back
    that same family (None).
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
    """Suggest installed family names that contain `query` as a substring when no exact match is found."""
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
    """Human-readable name for an OpenType `script` tag, e.g. `arab` -> `Arabic` and so on."""
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
    """Human-readable name for an OpenType `language` tag, e.g. `ARA ` -> `Arabic`."""
    code = OT_LANGUAGE_TAGS.get(tag)
    if not code:
        return tag.strip()
    try:
        return Language.match(code).name
    except LanguageNotFoundError:
        return tag.strip()


def _scripts_supported(font: TTFont) -> list[tuple[str, str]]:
    """
    Every script and script/language-system combination declared across GSUB and GPOS.

    Inspired by `otfinfo -s` which shows one entry per script tag + one entry per non-default language
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
    """Name-table and general font info."""
    name = font["name"]

    def debug(name_id: NameID) -> str | None:
        return name.getDebugName(name_id)

    family, subfamily = debug(NameID.FAMILY), debug(NameID.SUBFAMILY)
    pref_family, pref_subfamily = debug(NameID.PREFERRED_FAMILY), debug(NameID.PREFERRED_SUBFAMILY)

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
        ("Family", f"{family} " + f"({pref_family})" if pref_family and pref_family != family else ""),
        (
            "Subfamily",
            f"{subfamily} " + f"({pref_subfamily})" if pref_subfamily and pref_subfamily != subfamily else "",
        ),
        ("Full name", debug(NameID.FULL_NAME)),
        ("PS1 name", debug(NameID.POSTSCRIPT_NAME)),
        ("Font type", outline),
        ("Units/Em", str(font["head"].unitsPerEm) if "head" in font else None),
        ("Glyphs", str(font["maxp"].numGlyphs) if "maxp" in font else None),
        (
            "Weight/Width",
            f"{font['OS/2'].usWeightClass} / {font['OS/2'].usWidthClass}" if "OS/2" in font else None,
        ),
        ("Version", debug(NameID.VERSION).split(";")[0] if debug(NameID.VERSION) else None),
        # ("Unique ID", debug(NameID.UNIQUE_ID)),
        ("Manufacturer", debug(NameID.MANUFACTURER)),
        ("Designer", debug(NameID.DESIGNER)),
        ("Vendor URL", debug(NameID.VENDOR_URL)),
        ("Designer URL", debug(NameID.DESIGNER_URL)),
        ("Licence", debug(NameID.LICENSE)),
        # ("Licence URL", debug(NameID.LICENSE_URL)),
        (
            "Copyright",
            debug(NameID.COPYRIGHT).replace("All rights reserved", "").rstrip(". ")
            if debug(NameID.COPYRIGHT)
            else None,
        ),
        ("Trademark", debug(NameID.TRADEMARK)),
    ]
    return {label: value for label, value in fields if value}


@dataclass
class FontData:
    info: dict[str, str]
    tables: dict[str, list[str]]
    scripts: list[tuple[str, str]]
    cv_variations: dict[str, int]
    nalt_counts: list[int]


def _character_variant_counts(font: TTFont) -> dict[str, int]:
    """
    Number of named values each declared Character Variant (cv01..cv99) which was read from its
    FeatureParams table.

    Optional per the OpenType spec, so most entries won't have one.

    Returns
    =======
    A dict mapping cvXX tags to the number of named values they declare, e.g. `{"cv01": 2, "cv02": 1}`.
    """
    counts: dict[str, int] = {}
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        feature_list = font[table_tag].table.FeatureList
        if feature_list is None:
            continue
        for record in feature_list.FeatureRecord:
            if not CV_TAG_RE.match(record.FeatureTag):
                continue
            num_params = getattr(record.Feature.FeatureParams, "NumNamedParameters", 0)
            if num_params:
                counts[record.FeatureTag] = max(counts.get(record.FeatureTag, 0), num_params)
    return counts


def _feature_lookup_indices(font: TTFont, tag: str) -> set[int]:
    """Every LookupList index referenced by `tag`'s FeatureRecord(s) across GSUB/GPOS."""
    indices: set[int] = set()
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        feature_list = font[table_tag].table.FeatureList
        if feature_list is None:
            continue
        indices.update(
            index
            for record in feature_list.FeatureRecord
            if record.FeatureTag == tag
            for index in record.Feature.LookupListIndex
        )
    return indices


def _annotation_alternate_counts(font: TTFont) -> list[int]:
    """
    Distinct counts of glyph alternates the `nalt` (Annotation) feature offers, across every
    glyph it applies to.

    `nalt` generally lives per-glyph in its AlternateSubst lookup, so we have to iterate every subtable and every glyph's alternates to find the distinct counts.
    """
    if "GSUB" not in font:
        return []
    lookup_list = font["GSUB"].table.LookupList
    if lookup_list is None:
        return []

    counts: set[int] = set()
    for index in _feature_lookup_indices(font, "nalt"):
        lookup = lookup_list.Lookup[index]
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            alternates = getattr(subtable, "alternates", None)
            if alternates:
                counts.update(len(alts) for alts in alternates.values())
    return sorted(counts)


def _read_font_data(path: str, index: int) -> FontData:
    """Parse a font file's info, GSUB/GPOS feature tags and supported scripts.

    Returns
    =======
    A FontData object with the font's name table info, GSUB/GPOS feature
    """
    font = TTFont(path, fontNumber=index, lazy=True)

    tables: dict[str, list[str]] = {}
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        feature_list = font[tag].table.FeatureList
        if feature_list is not None:
            tables[tag] = sorted({record.FeatureTag for record in feature_list.FeatureRecord})

    return FontData(
        info=_font_info(font),
        tables=tables,
        scripts=_scripts_supported(font),
        cv_variations=_character_variant_counts(font),
        nalt_counts=_annotation_alternate_counts(font),
    )


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
        return await ctx.reply(await ctx.format_usage())

    t_start = time.monotonic()
    styles = await resolve_font_styles(query)
    if not styles:
        suggestions = await suggest_families(query)
        if suggestions:
            suggestion_text = "\n".join(f"- {bf(discord.utils.escape_mentions(s))}" for s in suggestions)
            return await ctx.reply(
                f"No font family found matching {bf(query)} exactly. Did you mean:\n\n{suggestion_text}",
            )
        return await ctx.reply(
            f"No font found matching {bf(query)}.\n"
            f"Try `{await ctx.best_prefix()}findfont --name {query}` to search by name.",
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
    footnote_text = f"{Path(chosen.file).name} · {chosen.style}"

    if (flags["fontspec"] or flags["fs"]) and all_tags:
        grouped: dict[str, list[str]] = {}
        for tag in all_tags:
            group = group_for(tag)
            grouped.setdefault(group, []).extend(display_values(tag, group, data.cv_variations, data.nalt_counts))

        lines: list[str] = []
        for group in (*FEATURE_GROUPS.keys(), OTHER_GROUP):
            if group not in grouped:
                continue
            values_fmt = " ".join(f"`{value}`" for value in grouped[group])
            lines.append(f"{bf(group)}\n-# {values_fmt}")

        title_text = f"OpenType features for `fontspec`\n{footnote(footnote_text)}"
        ctx.log(f"fontfeatures finished in {time.monotonic() - t_start:.3f}s.", context="fonts", level=logging.DEBUG)
        return await ctx.pager_v2(content=lines, title=title_text, code=False, maxheight=25)

    features_text = " ".join(f"`{tag}`" for tag in all_tags) if all_tags else "None declared"
    tag_length = max((len(tag) for tag, label in data.scripts), default=0)
    scripts_text = (
        "\n".join(f"`{tag:<{tag_length}}` {label}" for tag, label in data.scripts) if data.scripts else "None declared"
    )

    lines = [
        f"{bf('Font info')}",
        tabulate(data.info),
        "",
        f"{bf('OpenType features')}",
        features_text,
        "",
        f"{bf('Scripts supported')}",
        scripts_text,
    ]

    title_text = f"Font Features\n{footnote(footnote_text)}"
    ctx.log(f"fontfeatures finished in {time.monotonic() - t_start:.3f}s.", context="fonts", level=logging.DEBUG)
    return await ctx.pager_v2(content=lines, title=title_text, code=False, maxheight=30)
