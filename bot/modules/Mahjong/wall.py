"""
A shuffled single-player tile wall, for the interactive drawer.
"""

import random

from .tiles import HAND_TILE_NAMES


class WallEmptyError(RuntimeError):
    """Raised when trying to draw from an exhausted wall."""


def _full_set() -> list[str]:
    return [tile for tile in HAND_TILE_NAMES for _ in range(4)]


class Wall:
    """A shuffled 136-tile wall (34 kinds x4), drawn one at a time."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()
        self._tiles: list[str] = _full_set()
        self._rng.shuffle(self._tiles)

    @property
    def remaining(self) -> int:
        return len(self._tiles)

    def draw(self) -> str:
        if not self._tiles:
            raise WallEmptyError("The wall is empty.")
        return self._tiles.pop()

    def draw_many(self, n: int) -> list[str]:
        return [self.draw() for _ in range(n)]
