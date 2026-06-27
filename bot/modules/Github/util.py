import re

import discord
from github.Repository import Repository
from utils.lib import split_text

from .GithubColours import GITHUB_LANG2COLOUR


async def _gh_pagination(
    text,
    basetitle="",
    header=None,
    colour=discord.Color.from_str("#0FBF3E"),
    syntax="latex",
):
    blocks: list[str] = []
    if text:
        blocks = split_text(text, 1000, code=True, syntax=syntax)
    else:
        blocks = [""]
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


async def gh_view_pagination(ctx, text, title, start_page=0, **pagination_args):
    pages = await _gh_pagination(text, basetitle=title, **pagination_args)

    msg = await ctx.pager(pages, start_page=start_page, locked=False)

    return msg


async def _syntax_selection(filename) -> str:
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


def lang2colour(repo: Repository) -> discord.Colour:
    """Outputs a colour to be rendered for the layout view depending on the language field in the returned JSON of github API object

    Args:
        repo (Repository): The GitHub repository object

    Returns:
        discord.Colour: The colour to be used for the layout view
    """
    language: str = repo.language
    return GITHUB_LANG2COLOUR.get(language, discord.Color.from_str("#0FBF3E"))


async def sanitise_image(text: str) -> str:
    """
    Sanitise the image formatting embedded within a Github issue/PR-context test.

    Github Issues generally contain two types of images in the raw markdown
    ```
    <img width ... src="[URL]" or ![image](URL)
    ```

    We use regex to replace these with just the url, as the former is not supported by discord embeds and the latter is not supported in raw markdown

    Args:
        text (str): The text to be sanitised

    Returns:
        str: The sanitised text, with the image formatting removed and replaced with just the image URL
    """
    # pattern for <img width ... src=[URL]>
    html_img_pattern = r'<img.*?src=["\'](.*?)["\'].*?>'
    text = re.sub(html_img_pattern, r"\1", text)

    # pattern for ![image](URL)
    markdown_img_pattern = r"!\[.*?\]\((.*?)\)"
    text = re.sub(markdown_img_pattern, r"\1", text)

    # finally, purge html/markdown comments
    comment_pattern = r"<!--.*?-->"
    text = re.sub(comment_pattern, "", text)

    return text


async def grab_image(text: str) -> list[str] | None:
    """
    Grab image URLs from a Github issue/PR-context text.

    Args:
        text (str): Text from which the URLs are to be extracted.

    Returns:
        list[str] | None: A list of image URLs found in the text, or None if no URLs are found.
    """
    images: list[str] = []

    html_img_pattern = r'<img.*?src=["\'](.*?)["\'].*?>'
    images.extend(re.findall(html_img_pattern, text))
    markdown_img_pattern = r"!\[.*?\]\((.*?)\)"
    images.extend(re.findall(markdown_img_pattern, text))

    return images if images else None


def _grab_image(text: str) -> list[str] | None:
    """
    Grab image URLs from a Github issue/PR-context text.

    Args:
        text (str): Text from which the URLs are to be extracted.

    Returns:
        list[str] | None: A list of image URLs found in the text, or None if no URLs are found.
    """
    images: list[str] = []

    html_img_pattern = r'<img.*?src=["\'](.*?)["\'].*?>'
    images.extend(re.findall(html_img_pattern, text))
    markdown_img_pattern = r"!\[.*?\]\((.*?)\)"
    images.extend(re.findall(markdown_img_pattern, text))

    return images if images else None
