"""
Notation for declared melds (tiles shown face-up because they were called),
as distinct from the concealed remainder of a hand.

Bracketed groups are pulled out of the hand text before the ordinary tile
tokeniser (`tiles.parse_hand`) sees it, but the contents of each bracket are
still parsed with that same tokeniser, so meld tiles use the exact same
compact notation as everything else:

    [123m]   an open run (chi) or triplet (pon) or open kan (minkan/shouminkan)
             - 3 identical tiles -> open triplet
             - 3 consecutive same-suit tiles -> open run
             - 4 identical tiles -> open kan
    (1111z)  a closed kan (ankan) - always exactly 4 identical tiles.
             Concealed despite being "shown", since ankan doesn't break menzen.
"""

from __future__ import annotations

import re

from .hand import Group
from .tiles import MahjongParseError, number_of, parse_hand, suit_of

_MELD_RE = re.compile(r"\[([^\]]*)\]|\(([^)]*)\)")


def _parse_open_meld(raw: str) -> Group:
    tiles = parse_hand(raw)
    kinds = set(tiles)

    if len(tiles) == 3 and len(kinds) == 1:
        return Group("triplet", tile=tiles[0], concealed=False)

    if len(tiles) == 4 and len(kinds) == 1:
        return Group("kan", tile=tiles[0], concealed=False)

    if len(tiles) == 3 and len(kinds) == 3:
        suit = suit_of(tiles[0])
        if suit is None or any(suit_of(t) != suit for t in tiles):
            raise MahjongParseError(f"`[{raw}]` isn't a valid meld: a run must be one suit.")
        numbers = sorted(number_of(t) for t in tiles)
        if numbers[0] + 1 != numbers[1] or numbers[1] + 1 != numbers[2]:
            raise MahjongParseError(f"`[{raw}]` isn't a valid meld: a run must be three consecutive tiles.")
        return Group("sequence", suit=suit, start=numbers[0], concealed=False)

    raise MahjongParseError(f"`[{raw}]` isn't a valid meld: expected a 3-tile run/triplet or a 4-tile kan.")


def _parse_ankan(raw: str) -> Group:
    tiles = parse_hand(raw)
    if len(tiles) != 4 or len(set(tiles)) != 1:
        raise MahjongParseError(f"`({raw})` isn't a valid closed kan: expected four identical tiles.")
    return Group("kan", tile=tiles[0], concealed=True)


def extract_melds(text: str) -> tuple[str, list[Group]]:
    """
    Pull every `[...]`/`(...)` meld out of `text`, returning the remaining
    text (for the concealed portion + winning tile, still parsed normally by
    `tiles.parse_hand`) alongside the list of declared melds.
    """
    melds: list[Group] = []

    def _replace(match: re.Match) -> str:
        open_body, closed_body = match.group(1), match.group(2)
        melds.append(_parse_open_meld(open_body) if open_body is not None else _parse_ankan(closed_body))
        return " "

    remaining = _MELD_RE.sub(_replace, text)
    return remaining, melds
