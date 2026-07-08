from __future__ import annotations

from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Any

ScoreLine = namedtuple("ScoreLine", "name points note")


class ScoringError(ValueError):
    """Raised when the given tiles don't form a valid, scoreable winning hand."""


class Ruleset(ABC):
    """A scoring ruleset: takes raw hand text (+ ruleset-specific flags), returns a result."""

    @abstractmethod
    def compute(self, text: str, **flags: Any) -> Any: ...
