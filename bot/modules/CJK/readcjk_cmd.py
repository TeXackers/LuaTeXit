from cmdClient import Context
from cmdClient.Format import remove_markdown_delimiters
from cmdClient.Layouts import Body, Footer, Header, TextEmbed
from constants import LuaTeXitCC
from discord.ui import Container, Separator

from .module import cjk_module as module
from .resources import ReadingKey, transliterate

# (transliterate() reading key, display label, flags that select it)
LANGUAGES: list[tuple[ReadingKey, str, tuple[str, ...]]] = [
    (ReadingKey("cantonese"), "Cantonese", ("c",)),
    (ReadingKey("mandarin"), "Mandarin", ("p", "m")),
    (ReadingKey("korean"), "Korean", ("k",)),
    (ReadingKey("vietnamese"), "Vietnamese", ("v",)),
]

BODY_LIMIT = 1000


@module.cmd(
    "readcjk",
    desc="Transliterates CJK text into Cantonese, Mandarin, Korean, or Vietnamese readings.",
    aliases=["read"],
    flags=["c", "m", "p", "k", "v"],
)
async def cmd_readcjk(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}readcjk <text> [-c] [-m] [-p] [-k] [-v]
    Description:
        Renders CJK text as its Cantonese, Mandarin, Korean, and/or Vietnamese reading. Shows all four if no flag is given; multiple flags may be combined.
    Flags::
        c: Cantonese (Jyutping).
        p/m: Mandarin / Putonghua (Pinyin).
        k: Korean (Hangul).
        v: Vietnamese (Hán Việt).
    Examples``:
        {prefix}readcjk 滾滾長江東逝水
        {prefix}readcjk 滾滾長江東逝水 -c
        {prefix}readcjk 滾滾長江東逝水 -c -p
    """
    text = remove_markdown_delimiters(ctx.args.strip()).replace("```", "").strip()
    if not text:
        return await ctx.error_reply("Please provide some CJK text to transliterate.")

    selected = [(reading, label) for reading, label, flag_names in LANGUAGES if any(flags[f] for f in flag_names)]
    if not selected:
        selected = [(reading, label) for reading, label, _ in LANGUAGES]

    results = [(label, transliterate(text, reading)) for reading, label in selected]

    # add original text to body
    body = f"Original Text\n```\n{text}\n```\n"
    body += "\n".join(f"» {label}\n```\n{translit}\n```" for label, translit in results)
    footer = f"Requested by {ctx.author}"

    if len(body) <= BODY_LIMIT:
        header = f"Transliteration"
        return await ctx.reply(
            view=TextEmbed(
                header=header,
                body=body,
                footer=footer,
                accent_colour=LuaTeXitCC["cyan"],
            ),
        )

    pages = [
        Container(
            Header("» " + label),
            Separator(),
            Body(text),
            Separator(),
            Body(translit),
            Footer(footer),
            accent_colour=LuaTeXitCC["cyan"],
        )
        for label, translit in results
    ]
    return await ctx.pager_v2_pages(pages)
