from modules.Mahjong.tiles import MahjongParseError

from .base import Ruleset, ScoreLine, ScoringError
from .context import HandContext, build_context
from .hongkong import HongKongRuleset, ScoreFlags, ScoreResult
from .riichi import RiichiFlags, RiichiRuleset, RiichiScoreResult, describe_yakuman

compute_score = HongKongRuleset().compute

__all__ = [
    "HandContext",
    "HongKongRuleset",
    "MahjongParseError",
    "RiichiFlags",
    "RiichiRuleset",
    "RiichiScoreResult",
    "Ruleset",
    "ScoreFlags",
    "ScoreLine",
    "ScoreResult",
    "ScoringError",
    "build_context",
    "compute_score",
    "describe_yakuman",
]
