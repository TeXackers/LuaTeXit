"""
Decomposition of a 14-tile hand into scoring shapes.

A "group" is one of:
- ("triplet", tile): three identical tiles
- ("sequence", suit, start): three consecutive suited tiles, start..start+2

A standard decomposition is a dict {"pair": tile, "groups": [group, group, group, group]}.
Since a hand can often be grouped more than one valid way, `decompose_hand` returns every valid decomposition; callers pick whichever scores best.
"""

from __future__ import annotations

from collections import Counter

from .tiles import DRAGONS, SUITS, WINDS, number_of, suit_of

Group = tuple
Decomposition = dict


def is_seven_pairs(hand_tiles: list[str]) -> bool:
    counts = Counter(hand_tiles)
    return len(counts) == 7 and all(c == 2 for c in counts.values())


_ORPHAN_KINDS: set[str] = {f"1{suit}" for suit in SUITS} | {f"9{suit}" for suit in SUITS} | set(WINDS) | set(DRAGONS)


def is_thirteen_orphans(hand_tiles: list[str]) -> bool:
    counts = Counter(hand_tiles)
    if set(counts) != _ORPHAN_KINDS:
        return False
    return sorted(counts.values()) == [1] * 12 + [2]


def _decompose_groups(counts: dict[str, int]) -> list[list[Group]]:
    """Recursively split `counts` into groups of 3."""

    tile = next((t for t, c in counts.items() if c > 0), None)
    if tile is None:
        return [[]]

    results: list[list[Group]] = []

    if counts[tile] >= 3:
        counts[tile] -= 3
        results.extend([("triplet", tile), *rest] for rest in _decompose_groups(counts))
        counts[tile] += 3

    suit = suit_of(tile)
    if suit is not None:
        n = number_of(tile)
        second, third = f"{n + 1}{suit}", f"{n + 2}{suit}"
        if n <= 7 and counts.get(second, 0) > 0 and counts.get(third, 0) > 0:
            counts[tile] -= 1
            counts[second] -= 1
            counts[third] -= 1
            results.extend([("sequence", suit, n), *rest] for rest in _decompose_groups(counts))
            counts[tile] += 1
            counts[second] += 1
            counts[third] += 1

    return results


def decompose_hand(hand_tiles: list[str]) -> list[Decomposition]:
    """
    Every valid (pair, 4 groups) decomposition of a 14-tile standard hand.
    Returns an empty list if the hand doesn't decompose this way at all
    (it might still be seven pairs or thirteen orphans).
    """
    if len(hand_tiles) != 14:
        raise ValueError("A hand must have exactly 14 tiles (flowers don't count toward this).")

    counts = dict(Counter(hand_tiles))
    decompositions: list[Decomposition] = []

    for pair_tile, cnt in list(counts.items()):
        if cnt >= 2:
            counts[pair_tile] -= 2
            decompositions.extend(
                {"pair": pair_tile, "groups": groups} for groups in _decompose_groups(counts) if len(groups) == 4
            )
            counts[pair_tile] += 2

    return decompositions
