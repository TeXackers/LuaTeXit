from cmdClient import Context  # noqa
from cmdClient.Layouts import TextEmbed
from constants import LuaTeXitCC
from utils.lib import tabulate

from .module import cjk_module as module
from .resources import lookup

VARIANT_LABELS = {
    "kSimplifiedVariant": "Simplified",
    "kTraditionalVariant": "Traditional",
    "kSemanticVariant": "Semantic",
    "kSpecializedSemanticVariant": "Specialised semantic",
    "kZVariant": "Z-variant",
    "kJapaneseNewVariant": "Japanese New",
    "kSpoofingVariant": "Looks like",
}


def _variant_str(variant: dict) -> str:
    part = f"{variant['char']} ({variant['codepoint']})"
    # if variant.get("source"):
    #     part += f" via {variant['source']}"
    return part


@module.cmd(
    "han",
    desc="Looks up a Han character's definition, readings and variants.",
    aliases=["hanzi", "kanji", "hanja"],
)
async def cmd_han(ctx: Context):
    """
    Usage``:
        {prefix}han <character>
    Description:
        Looks up a single Han character in the Unihan database, showing its definition, readings in a variety of ways plus reconstructed Tang-era Chinese, and any recorded variants.
    Examples``:
        {prefix}han 逝
        {prefix}han 雄
    """
    char = ctx.args.strip()
    if not char:
        return await ctx.error_reply("Please provide a Han character to look up, e.g. `han 雄`.")
    if len(char) != 1:
        return await ctx.error_reply("Please provide exactly one character at a time.")

    entry = lookup(char)
    if entry is None:
        return await ctx.error_reply(f"No Unihan entry found for `{char}`.")

    readings = entry.get("readings", {})
    pron = entry.get("pronunciations", {})
    variants = entry.get("variants", {})

    fields = {}
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
        fields["Korean"] = f"{', '.join(hangul)} ({', '.join(romanized).lower()})" if romanized else ", ".join(hangul).lower()
    if vietnamese := pron.get("vietnamese"):
        fields["Vietnamese"] = ", ".join(vietnamese)
    # if tang := readings.get("kTang"):
    #     fields["Tang Chinese"] = ", ".join(tang)
    # if fanqie := readings.get("kFanqie"):
    #     fields["Fanqie"] = ", ".join(fanqie)

    body = tabulate(fields) if fields else "No readings recorded."

    variant_lines = [
        f"**{label}:** {', '.join(_variant_str(v) for v in variants[key])}"
        for key, label in VARIANT_LABELS.items()
        if variants.get(key)
    ]
    if variant_lines:
        body += "\n### Variants\n" + "\n".join(variant_lines)

    return await ctx.reply(
        view=TextEmbed(
            header=f"{char} ([{entry['codepoint']}](https://util.unicode.org/UnicodeJsps/character.jsp?a={entry['codepoint'][2:]}))",
            body=body,
            footer=f"Requested by {ctx.author}",
            accent_colour=LuaTeXitCC["yellow"],
        ),
    )
