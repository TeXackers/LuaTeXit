"""
Generic context for every ruleset: turns raw hand text into a `HandContext`
using the same tokeniser `;score` has always used (`tiles.parse_hand`), plus
the new meld notation (`melds.extract_melds`). Rulesets branch out from here.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.Mahjong.melds import extract_melds
from modules.Mahjong.tiles import parse_hand

from .base import ScoringError

if TYPE_CHECKING:
    from modules.Mahjong.hand import Group


@dataclass
class HandContext:
    concealed_tiles: list[str]
    melds: list[Group]
    winning_tile: str
    all_tiles: list[str]  # concealed + meld tiles flattened

    @property
    def concealed(self) -> bool:
        """Whether the *hand* is concealed (menzen) - false if any meld is open (ankan doesn't count)."""
        return all(m.concealed for m in self.melds)


def build_context(text: str) -> HandContext:
    remaining, melds = extract_melds(text)
    concealed_tiles = parse_hand(remaining)

    expected_concealed = 14 - 3 * len(melds)
    if len(concealed_tiles) != expected_concealed:
        meld_tile_count = sum(len(m.physical_tiles()) for m in melds)
        total = len(concealed_tiles) + meld_tile_count
        raise ScoringError(
            f"Found {total} tiles total ({len(concealed_tiles)} concealed + {meld_tile_count} in melds), "
            "but a complete hand needs 14 tiles plus 1 more per kan.",
        )

    all_tiles = concealed_tiles + [t for m in melds for t in m.physical_tiles()]

    return HandContext(
        concealed_tiles=concealed_tiles,
        melds=melds,
        winning_tile=concealed_tiles[-1],
        all_tiles=all_tiles,
    )
