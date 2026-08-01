import json

from cmdClient import Context
from cmdClient.Format import bf, heading, hyperlink, remove_markdown_delimiters
from cmdClient.Layouts import TextEmbed
from constants import LuaTeXitCC
from utils.lib import tabulate

from .module import cjk_module as module
from .resources import Char, Codepoint, Designations, Variant, lookup

VARIANT_LABELS = {
    "kSimplifiedVariant": "Simplified",
    "kTraditionalVariant": "Traditional",
    "kSemanticVariant": "Semantic",
    "kSpecializedSemanticVariant": "Special",
    "kZVariant": "Z-variant",
    "kJapaneseNewVariant": "Japanese New",
    "kSpoofingVariant": "Confused for",
    "kCCCIIVariant": "Related form",
}
UNICODE_LOOKUP_URL = "https://util.unicode.org/UnicodeJsps/character.jsp?a={}"


def _designation_table(designations: Designations) -> str:
    """
    Renders the lists a character is designated under, grouped by country.

    Parameter
    ---------
    designations: dict
        The designations dictionary from a Unihan entry.

    Returns
    -------
    str
        A string containing a table of designations, or an empty string if there are none.
    """
    korea = []
    if tier := designations.get("korean_education"):
        if tier == "중학교용":
            korea.append("初級 (基礎漢字)")
        elif tier == "고등학교용":
            korea.append("高級 (基礎漢字)")
        else:
            korea.append(f"基礎漢字")
    if exam := designations.get("hanja_exam"):
        korea.append(f"語文會{exam}")
    # if none of the above, then use KoreanName
    if designations.get("korean_name") and len(korea) == 0:
        korea.append("人名用漢字")

    japan = []
    if grade := designations.get("joyo"):
        japan.append(f"{grade} (常用漢字)")
    if designations.get("jinmeiyo"):
        japan.append("人名用漢字")

    hong_kong = []
    if grade := designations.get("hong_kong_grade"):
        hong_kong.append(f"{grade}年級 (小學學習字詞表)")

    china = []
    if level := designations.get("tgh_level"):
        tier_hanzi = {1: "一", 2: "二", 3: "三"}[level]
        china.append(f"{tier_hanzi}级 (通用规范汉字表)")

    rows = {
        label: ", ".join(parts)
        for label, parts in (
            ("China", china),
            ("Hong Kong", hong_kong),
            ("Japan", japan),
            ("Korea", korea),
        )
        if parts
    }
    return tabulate(rows) if rows else ""


def _codepoint_to_url(codepoint: Codepoint) -> str:
    """
    Converts a codepoint string like 'U+4E00' to a markdown hyperlink.
    """
    return hyperlink(
        codepoint,
        UNICODE_LOOKUP_URL.format(codepoint[2:]),
    )


def _variant_str(variant: Variant) -> str:
    return f"{variant['char']} ({_codepoint_to_url(variant['codepoint'])})"


@module.cmd(
    "han",
    desc="Looks up a Han character's definition, readings and variants.",
    aliases=["hanzi", "kanji", "hanja"],
    flags=["raw", "r"],
)
async def cmd_han(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}han <character> [--raw|-r]
    Description:
        Looks up a single Han character in the Unihan database, showing its definition, readings in a variety of ways plus reconstructed Tang-era Chinese, and any recorded variants.
    Flags::
        raw: Show the raw Unihan entry as JSON instead.
    Examples``:
        {prefix}han 逝
        {prefix}han 雄
        {prefix}han 雄 --raw
    """
    char = remove_markdown_delimiters(ctx.args.strip()).strip()
    if not char:
        return await ctx.error_reply("Please provide a Han character to look up, e.g. `han 雄`.")
    if len(char) != 1:
        return await ctx.error_reply("Please provide exactly one character at a time.")
    char = Char(char)

    entry = lookup(char)
    if entry is None:
        return await ctx.error_reply(f"No Unihan entry found for `{char}`.")

    if flags["raw"] or flags["r"]:
        return await ctx.pager_v2(
            json.dumps(entry, indent=2, ensure_ascii=False),
            title=f"Raw Unihan entry for {char}",
            code=True,
            syntax="json",
        )

    readings = entry.get("readings", {})
    pron = entry.get("pronunciations", {})
    variants = entry.get("variants", {})

    fields: dict[str, str] = {}
    fields["Unicode"] = _codepoint_to_url(entry["codepoint"])
    if defn := readings.get("kDefinition"):
        fields["Definition"] = defn
    if mandarin := pron.get("mandarin"):
        fields["Mandarin"] = ", ".join(mandarin)
    if cantonese := pron.get("cantonese"):
        fields["Cantonese"] = ", ".join(cantonese)
    if on := pron.get("japanese_on"):
        fields["Japanese (on)"] = ", ".join(on).lower()
    if kun := pron.get("japanese_kun"):
        fields["Japanese (kun)"] = ", ".join(kun).lower()
    if hangul := pron.get("korean_hangul"):
        romanized = pron.get("korean_romanized")
        fields["Korean"] = (
            f"{', '.join(hangul)} ({', '.join(romanized).lower()})" if romanized else ", ".join(hangul).lower()
        )
    if vietnamese := pron.get("vietnamese"):
        fields["Vietnamese"] = ", ".join(vietnamese)
    # if tang := readings.get("kTang"):
    #     fields["Tang Chinese"] = ", ".join(tang)
    # if fanqie := readings.get("kFanqie"):
    #     fields["Fanqie"] = ", ".join(fanqie)

    body = tabulate(fields) if fields else "No readings recorded."

    # populate variants that do not share the same codepoint
    variant_lines = []
    for key, label in VARIANT_LABELS.items():
        others = [v for v in variants.get(key, []) if v["codepoint"] != entry["codepoint"]]
        if others:
            variant_lines.append(f"{bf(label)}: {', '.join(_variant_str(v) for v in others)}")

    if designation_table := _designation_table(entry.get("designations", {})):
        body += f"\n{heading('Designations', 3)}\n" + designation_table

    if variant_lines:
        body += f"\n{heading('Variants', 3)}\n" + "\n".join(variant_lines)

    return await ctx.reply(
        view=TextEmbed(
            header=f"{char}",
            body=body,
            footer=f"Requested by {ctx.author}",
            accent_colour=LuaTeXitCC["yellow"],
        ),
    )
