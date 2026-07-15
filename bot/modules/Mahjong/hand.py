"""
Decomposition of a hand into scoring shapes.

A "group" is a `Group` covering one of:
- kind="triplet": three (or four, for a kan) identical tiles
- kind="sequence": three consecutive suited tiles, start..start+2

Groups carry a `concealed` flag so callers can tell an ankou/ankan (found purely within the concealed tiles) apart from a pon/chi/minkan meld shown face-up (see `melds.py`), which matters for Riichi fu/yaku but not for the groups `decompose_hand` itself produces (always concealed=True; melds are merged in separately by callers).

A standard decomposition is a dict {"pair": tile, "groups": [Group, ...]}.
Since a hand can often be grouped more than one valid way, `decompose_hand`
returns every valid decomposition; callers pick whichever scores best.
"""

from collections import Counter
from dataclasses import dataclass

from .tiles import DRAGONS, SUITS, WINDS, number_of, suit_of

Decomposition = dict


@dataclass(frozen=True)
class Group:
    kind: str  # "sequence" | "triplet" | "kan"
    tile: str | None = None  # for triplet/kan
    suit: str | None = None  # for sequence
    start: int | None = None  # for sequence
    concealed: bool = True

    def matches(self, kind: str, **attrs) -> bool:
        if self.kind != kind:
            return False
        return all(getattr(self, name) == value for name, value in attrs.items())

    def physical_tiles(self) -> list[str]:
        """The actual tile names making up this group (2x/3x/4x for triplet/kan)."""
        if self.kind == "sequence":
            return [f"{self.start + i}{self.suit}" for i in range(3)]
        if self.kind == "triplet":
            return [self.tile, self.tile, self.tile]
        if self.kind == "kan":
            return [self.tile, self.tile, self.tile, self.tile]
        raise ValueError(f"Unknown group kind `{self.kind}`.")


def has_group(groups: list[Group], kind: str, **attrs) -> bool:
    return any(g.matches(kind, **attrs) for g in groups)


def is_seven_pairs(hand_tiles: list[str]) -> bool:
    counts = Counter(hand_tiles)
    return len(counts) == 7 and all(c == 2 for c in counts.values())


ORPHAN_KINDS: set[str] = {f"1{suit}" for suit in SUITS} | {f"9{suit}" for suit in SUITS} | set(WINDS) | set(DRAGONS)


def is_thirteen_orphans(hand_tiles: list[str]) -> bool:
    """Useful for calculating 十三么 [HK]/国士無双 [Riichi]"""
    counts = Counter(hand_tiles)
    if set(counts) != ORPHAN_KINDS:
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
        results.extend([Group("triplet", tile=tile), *rest] for rest in _decompose_groups(counts))
        counts[tile] += 3

    suit = suit_of(tile)
    if suit is not None:
        n = number_of(tile)
        second, third = f"{n + 1}{suit}", f"{n + 2}{suit}"
        if n <= 7 and counts.get(second, 0) > 0 and counts.get(third, 0) > 0:
            counts[tile] -= 1
            counts[second] -= 1
            counts[third] -= 1
            results.extend([Group("sequence", suit=suit, start=n), *rest] for rest in _decompose_groups(counts))
            counts[tile] += 1
            counts[second] += 1
            counts[third] += 1

    return results


def decompose_hand(concealed_tiles: list[str], num_groups: int = 4) -> list[Decomposition]:
    """
    Every valid (pair, `num_groups` groups) decomposition of `concealed_tiles`.
    `num_groups` defaults to 4 (a full concealed hand); callers with declared melds pass `4 - len(melds)` since those groups are already accounted for.
    Returns an empty list if the tiles don't decompose this way at all (the
    hand might still be seven pairs or thirteen orphans, which don't call
    into this function at all).
    """
    if len(concealed_tiles) != num_groups * 3 + 2:
        raise ValueError(f"Expected {num_groups * 3 + 2} concealed tiles for {num_groups} groups + a pair.")

    ordered_tiles = sorted(concealed_tiles, key=lambda t: (suit_of(t) is None, suit_of(t) or "", number_of(t) or 0))
    counts = dict(Counter(ordered_tiles))
    decompositions: list[Decomposition] = []

    for pair_tile, cnt in list(counts.items()):
        if cnt >= 2:
            counts[pair_tile] -= 2
            decompositions.extend(
                {"pair": pair_tile, "groups": groups}
                for groups in _decompose_groups(counts)
                if len(groups) == num_groups
            )
            counts[pair_tile] += 2

    return decompositions
