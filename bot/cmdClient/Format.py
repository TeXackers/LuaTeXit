"""
Generic functions for formatting text.
"""

import builtins
from collections.abc import Iterable
from typing import Any

from discord.utils import escape_mentions


def heading(text: str, level: int) -> str:
    """Create a markdown-friendly heading

    Args:
        text (str): Text to become a heading
        level (int): Markdown heading level

    Raises:
        ValueError: if level < 1 or level > 3

    Returns:
        str: Formatted heading
    """
    # level must be between 1 and 3
    if int(level) < 1 or int(level) > 3:
        raise ValueError("Heading level must be between 1 and 3.")

    # validation
    if text.startswith(("#", "-#", "- ", "* ")):
        for prefix in ("-#", "- ", "* ", "#"):
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
                break

    return f"{'#' * level} {escape_mentions(text)}"


def h1(text: str) -> str:
    """Level 1 heading"""
    return heading(text, 1)


def h2(text: str) -> str:
    """Level 2 heading"""
    return heading(text, 2)


def h3(text: str) -> str:
    """Level 3 heading"""
    return heading(text, 3)


def footnote(text: str) -> str:
    """Footnote text"""
    if not text:
        return text
    return f"-# {text}"


def hyperlink(text: str, url: str) -> str:
    """Create a markdown-friendly hyperlink

    Args:
        text (str): Text to display
        url (str): URL to link to

    Returns:
        str: Formatted hyperlink
    """
    return f"[{text}]({url})"


def bf(text: str) -> str:
    """Embold text"""
    if not text:
        return text
    if text.startswith("**") and text.endswith("**"):
        return text
    return f"**{escape_mentions(text)}**"


def it(text: str) -> str:
    """Italicise text"""
    if not text:
        return text
    # ensure that it's not already delimited with asterisks/underscores
    if (text.startswith("*") and text.endswith("*")) or (text.startswith("_") and text.endswith("_")):
        return text
    return f"_{escape_mentions(text)}_"


def emph(text: str) -> str:
    """LaTeX-like emphasis"""
    # if it is already italicised, then reverse it
    # if it's upright, then italicise it
    if (text.startswith("*") and text.endswith("*")) or (text.startswith("_") and text.endswith("_")):
        return text.strip("*_")
    return f"_{escape_mentions(text)}_"


def quote(text: str) -> str:
    """Quote text"""
    if text.startswith("> "):
        return text
    return f"> {escape_mentions(text)}"


def itemise(it: Iterable[str]) -> str:
    """Itemise a list of strings"""
    return "\n".join(f"- {escape_mentions(item)}" for item in it)


def itemize(it: Iterable[str]) -> str:
    """Itemise a list of strings (alias for itemise)"""
    return itemise(it)


def enumerate(it: Iterable[Any], start: int = 1) -> str:  # noqa
    """Enumerate a list of strings"""
    return "\n".join(f"{i}. {escape_mentions(str(item))}" for i, item in builtins.enumerate(it, start=start))
