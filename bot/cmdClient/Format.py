"""
Generic functions for formatting text.
"""

from discord.utils import escape_mentions


def heading(text: str, level: int) -> str:
    # level must be between 1 and 5
    if level < 1 or level > 5:
        raise ValueError("Heading level must be between 1 and 5.")

    # validation
    if text.startswith("#"):
        text = text.lstrip("#").strip()
    elif text.startswith("-#"):
        text = text.lstrip("-#").strip()
    elif text.startswith("- "):
        text = text.lstrip("- ").strip()
    elif text.startswith("* "):
        text = text.lstrip("* ").strip()

    return f"{'#' * level} {escape_mentions(text)}"


def h1(text: str) -> str:
    return heading(text, 1)


def h2(text: str) -> str:
    return heading(text, 2)


def h3(text: str) -> str:
    return heading(text, 3)


def h4(text: str) -> str:
    return heading(text, 4)


def footnote(text: str) -> str:
    return f"-# {text}"


def hyperlink(text: str, url: str) -> str:
    return f"[{text}]({url})"
