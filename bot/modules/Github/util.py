import discord
from utils.lib import split_text


async def _gh_pagination(
    text,
    basetitle="",
    header=None,
    colour=discord.Color.from_str("#0FBF3E"),
    syntax="latex",
):
    blocks: list[str | None] = []
    if text:
        blocks = split_text(text, 1000, code=True, syntax=syntax)
    else:
        blocks = [None]

    embeds = []

    if len(blocks) == 1:
        block = blocks[0] if blocks[0] else ""
        if header:
            desc = f"{header}\n\n{block or ''}"
        else:
            desc = block if block else None

        embed = discord.Embed(title=basetitle, colour=colour, description=desc)
        embeds.append(embed)

    elif len(blocks) > 1:
        for i, block in enumerate(blocks):
            if header:
                desc = f"{header}\n\n{block or ''}"
            else:
                desc = block if block else None

            embed = discord.Embed(title=basetitle, colour=colour, description=desc)
            embed.set_footer(text=f"{i + 1} / {len(blocks)}")
            embeds.append(embed)

    return embeds


async def _gh_view_pagination(ctx, text, title, start_page=0, **pagination_args):
    pages = await _gh_pagination(text, basetitle=title, **pagination_args)

    msg = await ctx.pager(pages, start_page=start_page, locked=False)

    return msg


def _syntax_selection(filename) -> str:
    filetype = filename.split(".")[-1]
    match filetype:
        case "cfg" | "lua":
            return "lua"
        case "gitattributes" | "gitignore":
            return "gitignore"
        case "sty" | "cls" | "tex" | "tlg":
            return "latex"
        case "md":
            return "markdown"
        case "md5":
            return "md5"
        case "htm":
            return "html"
        case "rs" | "typ":
            return "rust"
        case "sh" | "bash" | "zsh":
            return "sh"
        case "bat" | "cmd":
            return "batch"
        case "rst":
            return "rst"
        case _:
            return ""
