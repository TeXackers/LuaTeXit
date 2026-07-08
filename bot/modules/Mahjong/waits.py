"""
Wait-shape detection: how the winning tile completed a standard decomposition.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from .tiles import number_of, suit_of

if TYPE_CHECKING:
    from .hand import Decomposition


def is_tanki(decomp: Decomposition, winning_tile: str) -> bool:
    """The winning tile completed the pair (was waiting alone)."""
    return decomp["pair"] == winning_tile


def is_shanpon(decomp: Decomposition, winning_tile: str) -> bool:
    """The winning tile completed a triplet out of what was a second pair."""
    if decomp["pair"] == winning_tile:
        return False
    return any(g.matches("triplet", tile=winning_tile) for g in decomp["groups"])


def classify_waits(decomp: Decomposition, winning_tile: str) -> list[str]:
    """
    Every way the winning tile could have completed this decomposition, by ways of "tanki", "shanpon", "kanchan", "penchan" or "ryanmen". A single physical grouping is often ambiguous about which tile was "the" winning one (e.g. a pair of 9m plus a 789m run could have been won on either the pair or the run) and each reading can score differently (notably for pinfu), so callers should score every one and keep the best.

    Raises ValueError if the winning tile doesn't fit this decomposition at all (caller error).
    """
    waits: list[str] = []
    if is_tanki(decomp, winning_tile):
        waits.append("tanki")
    if is_shanpon(decomp, winning_tile):
        waits.append("shanpon")

    suit = suit_of(winning_tile)
    n = number_of(winning_tile)
    if suit is not None:
        for g in decomp["groups"]:
            if g.kind == "sequence" and g.suit == suit and g.start <= n <= g.start + 2:
                if n == g.start + 1:
                    waits.append("kanchan")
                elif (g.start == 1 and n == g.start + 2) or (g.start == 7 and n == g.start):
                    waits.append("penchan")
                else:
                    waits.append("ryanmen")

    if not waits:
        raise ValueError(f"`{winning_tile}` doesn't complete this decomposition.")
    return waits


def is_kokushi_13_wait(hand_minus_winning: list[str], orphan_kinds: set[str]) -> bool:
    """13-sided wait: all 13 orphan kinds held once each, no pair yet."""
    counts = Counter(hand_minus_winning)
    return set(counts) == orphan_kinds and all(c == 1 for c in counts.values())


def is_chuuren_9_wait(hand_minus_winning: list[str], suit: str) -> bool:
    """
    9-sided wait: the pre-win 13 tiles are exactly 1112345678999 in one suit(純正九蓮宝燈), so any of the 9 numbers in that suit completes the hand.
    """
    expected = Counter({f"1{suit}": 3, f"9{suit}": 3, **{f"{n}{suit}": 1 for n in range(2, 9)}})
    return Counter(hand_minus_winning) == expected


def is_chuuren(tiles_14: list[str], suit: str) -> bool:
    """
    九蓮宝燈 in general (not necessarily the pure 9-wait variant): the complete 14-tile hand is 1112345678999 in one suit plus exactly one more tile from that same suit's 1-9 (i.e. it decomposes this way regardless of which of the 9 numbers was actually won on).
    """
    if len(tiles_14) != 14:
        return False
    counts = Counter(number_of(t) for t in tiles_14)
    if counts.get(1, 0) < 3 or counts.get(9, 0) < 3:
        return False
    if any(counts.get(n, 0) < 1 for n in range(2, 9)):
        return False
    excess = (counts.get(1, 0) - 3) + (counts.get(9, 0) - 3) + sum(counts.get(n, 0) - 1 for n in range(2, 9))
    return excess == 1
