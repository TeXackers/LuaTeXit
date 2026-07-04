"""
Shared helpers for rendering tiles as application emojis, used by both the
static scorer (scorer_cmd.py) and the interactive drawer (drawer_cmd.py).

Falls back to `` `tilename` `` text when a tile has no matching application
emoji (e.g. the emojis haven't been uploaded to the bot application yet).
"""

from __future__ import annotations

import re

from .tiles import ALL_TILE_NAMES

_TILE_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in sorted(ALL_TILE_NAMES, key=len, reverse=True)) + r")\b",
)


def tile_str(emojis_by_name: dict, tile: str) -> str:
    emoji = emojis_by_name.get(tile)
    return str(emoji) if emoji else f"`{tile}`"


def tiles_str(emojis_by_name: dict, tiles: list[str], sep: str = "") -> str:
    return sep.join(tile_str(emojis_by_name, t) for t in tiles)


def render_note(emojis_by_name: dict, note: str) -> str:
    """
    Swap in emojis for any exact tile names mentioned in a ScoreLine's note
    (e.g. "mai doesn't match your seat wind" -> "🎍 doesn't match your seat wind").
    Bare suit names (maan/tong/sak) aren't tile names on their own and are left as text.
    """
    return _TILE_NAME_RE.sub(lambda m: tile_str(emojis_by_name, m.group(0)), note)
