"""
Wait-shape detection: how the winning tile completed a standard decomposition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hand import Decomposition


def is_tanki(decomp: Decomposition, winning_tile: str) -> bool:
    """The winning tile completed the pair (was waiting alone)."""
    return decomp["pair"] == winning_tile


def is_shanpon(decomp: Decomposition, winning_tile: str) -> bool:
    """The winning tile completed a triplet out of what was a second pair."""
    if decomp["pair"] == winning_tile:
        return False
    return ("triplet", winning_tile) in decomp["groups"]
