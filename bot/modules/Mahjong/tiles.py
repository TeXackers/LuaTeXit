"""
Tile identity, compact notation parsing and formatting for the Mahjong module.

Compact notation (a la riichi/Tenhou shorthand) is accepted as input instead,
since typing e.g. `1maan,1maan,2maan,...` by hand is painful:

    m/p/s suffix: a run of digits followed by one suit letter expands to one
        tile per digit. `p` is used for tong (筒/pin) tiles. `s` is sak (索/sou), `m` is maan (萬/man). We respect the Cantonese nomenclature here.
        e.g. "123m" -> 1maan, 2maan, 3maan; "11p" -> 1tong, 1tong
    z suffix: a run of digits 1-7 indexes into HONOR_ORDER (winds then
        dragons), matching the common 1z..7z = 東南西北白發中 convention.
        e.g. "11z" -> east, east; "567z" -> 白發中
"""

import re
from collections import Counter

SUITS: tuple[str, ...] = ("maan", "tong", "sak")
SUIT_LETTERS: dict[str, str] = {"m": "maan", "p": "tong", "s": "sak"}

WINDS: list[str] = ["east", "south", "west", "north"]
DRAGONS: list[str] = ["white", "faat", "middle"]
HONOR_ORDER: list[str] = WINDS + DRAGONS

SUITED_TILES: list[str] = [f"{n}{suit}" for suit in SUITS for n in range(1, 10)]
HONOR_TILES: list[str] = WINDS + DRAGONS
HAND_TILE_NAMES: list[str] = SUITED_TILES + HONOR_TILES  # 34 kinds

_NAME_SET: set[str] = set(HAND_TILE_NAMES)
_GROUP_RE = re.compile(r"(\d+)([mpsz])", re.IGNORECASE)
_TOKEN_RE = re.compile(rf"^(?:{_GROUP_RE.pattern})+$", re.IGNORECASE)


class MahjongParseError(ValueError):
    """Raised when a hand string can't be parsed into tiles."""


def suit_of(tile: str) -> str | None:
    for suit in SUITS:
        if tile.endswith(suit):
            return suit
    return None


def number_of(tile: str) -> int | None:
    suit = suit_of(tile)
    if suit is None:
        return None
    return int(tile[: -len(suit)])


def is_wind(tile: str) -> bool:
    return tile in WINDS


def is_dragon(tile: str) -> bool:
    return tile in DRAGONS


def is_honor(tile: str) -> bool:
    return is_wind(tile) or is_dragon(tile)


def is_terminal(tile: str) -> bool:
    n = number_of(tile)
    return n in (1, 9)


def is_simple(tile: str) -> bool:
    n = number_of(tile)
    return n is not None and 2 <= n <= 8


def tile_sort_key(tile: str) -> tuple[int, int]:
    """Canonical display order: maan, tong, sak, then honours (winds, then dragons)."""
    suit = suit_of(tile)
    if suit is not None:
        return (SUITS.index(suit), number_of(tile))
    return (len(SUITS), HONOR_ORDER.index(tile))


def _expand_token(token: str) -> list[str]:
    """
    Expand one whitespace/`,`/`;`-delimited token into canonical tile names.

    A token may chain multiple (digits + suit-letter) groups back-to-back with
    no separator between them, matching how these hands are conventionally
    transcribed elsewhere (e.g. "123m456p789s11z" is one token, three groups).
    """
    low = token.lower()
    if low in _NAME_SET:
        return [low]

    if not _TOKEN_RE.match(token):
        raise MahjongParseError(f"Couldn't understand tile `{token}`.")

    tiles: list[str] = []
    for digits, suit in _GROUP_RE.findall(token):
        suit = suit.lower()
        for ch in digits:
            d = int(ch)
            if suit in SUIT_LETTERS:
                if not (1 <= d <= 9):
                    raise MahjongParseError(f"`{d}{suit}` isn't valid, suited tiles only go 1-9.")
                tiles.append(f"{d}{SUIT_LETTERS[suit]}")
            else:  # suit == "z"
                if not (1 <= d <= len(HONOR_ORDER)):
                    raise MahjongParseError(f"`{d}z` isn't valid, honors only go 1-{len(HONOR_ORDER)}.")
                tiles.append(HONOR_ORDER[d - 1])
    return tiles


def parse_hand(text: str) -> list[str]:
    """
    Parse a hand string (tiles delimited by `,`, `;`, newlines, and/or
    whitespace) into a flat list of canonical tile names, in the order given.

    The last tile in the resulting list is treated elsewhere as the winning
    tile (the one drawn or ronned), matching convention.
    """
    if not text or not text.strip():
        raise MahjongParseError("Please give me a hand to score.")

    tiles: list[str] = []
    for chunk in re.split(r"[,;\n]+", text):
        for token in chunk.split():
            tiles.extend(_expand_token(token))

    if not tiles:
        raise MahjongParseError("Please give me a hand to score.")

    return tiles


def counts_of(tiles: list[str]) -> Counter:
    return Counter(tiles)
