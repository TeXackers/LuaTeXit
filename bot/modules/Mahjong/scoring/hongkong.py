"""
Hong Kong mahjong scoring engine.

Everything derivable from the 14 tiles themselves (concealed-or-open read straight
off the `[...]`/`(...)` meld notation, same as riichi.py -- no separate flag) +
seat/round wind, tsumo-or-ron, and a handful of situational winning-condition
flags mirroring riichi.py's haitei/houtei/rinshan/chankan/tenhou/chiihou.
"""

from dataclasses import dataclass

from modules.Mahjong.hand import Group, decompose_hand, is_seven_pairs, is_thirteen_orphans
from modules.Mahjong.tiles import WINDS, is_dragon, is_honor, is_terminal, is_wind, suit_of
from modules.Mahjong.waits import is_chuuren

from .base import Ruleset, ScoreLine, ScoringError
from .context import build_context

MAX_FAAN = 13

_HALF_SPICY: dict[int, int] = {
    0: 1,
    1: 2,
    2: 4,
    3: 8,
    4: 16,
    5: 24,
    6: 32,
    7: 48,
    8: 64,
    9: 96,
    10: 128,
    11: 192,
    12: 256,
    13: 384,
}

# Names of the hand-tier patterns that already presume a fully concealed hand,
# so 門前清 shouldn't also be awarded on top of them.
_INHERENTLY_CONCEALED = {"四暗刻", "九子連環"}


@dataclass
class ScoreFlags:
    seat_wind: str = "east"
    round_wind: str = "east"
    zimo: bool = False  # tsumo, 自摸
    min_faan: int = 3
    cg: bool = False  # chankan, 搶槓, coeng gong
    hoidai: bool = False  # haitei, 海底撈月
    hodai: bool = False  # houtei, 河底撈魚
    gshf: bool = False  # rinshan, 槓上開花, gong soeng hoi faa
    gsg: bool = False  # doublekong, 槓上槓, gong soeng gong
    tinwu: bool = False  # tenhou, 天糊
    deiwu: bool = False  # chiihou, 地糊

    def __post_init__(self):
        if self.seat_wind not in WINDS:
            raise ScoringError(f"`{self.seat_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
        if self.round_wind not in WINDS:
            raise ScoringError(f"`{self.round_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
        if self.min_faan < 0:
            raise ScoringError("min_faan can't be negative.")
        if (self.hoidai or self.gshf or self.gsg) and not self.zimo:
            raise ScoringError("海底撈月/win-by-kong/double-kong are self-draw (zimo) wins, thus require zimo.")
        if (self.hodai or self.cg) and self.zimo:
            raise ScoringError("河底撈魚/robbing-the-kong are ron wins, not zimo.")
        if self.tinwu and not (self.zimo and self.is_dealer):
            raise ScoringError("Blessing of Heaven (天糊) requires being the dealer and winning by zimo.")
        if self.deiwu and not (self.zimo and not self.is_dealer):
            raise ScoringError("Blessing of Earth (地糊) requires being a non-dealer and winning by zimo.")

    @property
    def is_dealer(self) -> bool:
        return self.seat_wind == "east"


@dataclass
class ScoreResult:
    shape: str
    hand_tiles: list[str]
    winning_tile: str
    lines: list[ScoreLine]
    total: int  # total faan, capped at 13
    points: int  # faan converted to a score via the half-spicy table


def _points_for(total_faan: int, zimo: bool) -> int:
    table_points = _HALF_SPICY[total_faan]
    return round(table_points * 1.5) if zimo else table_points


def _score_generic(hand_tiles: list[str]) -> tuple[list[ScoreLine], list[ScoreLine]]:
    """Hand-tier faan derivable from the raw tile multiset alone, independent of
    how it's grouped. Returns (regular_lines, limit_lines)."""
    regular: list[ScoreLine] = []
    limit: list[ScoreLine] = []

    honors_present = any(is_honor(t) for t in hand_tiles)
    suits_present = {suit_of(t) for t in hand_tiles if suit_of(t)}
    single_suit = next(iter(suits_present)) if len(suits_present) == 1 else None

    if single_suit is not None:
        if honors_present:
            regular.append(ScoreLine("混一色", 3, "one suit + honours"))
        else:
            regular.append(ScoreLine("清一色", 7, "pure one suit"))

    if all(is_honor(t) for t in hand_tiles):
        limit.append(ScoreLine("字一色", 10, "every tile is an honour tile"))
    elif all(is_terminal(t) or is_honor(t) for t in hand_tiles):
        if honors_present:
            regular.append(ScoreLine("花幺九", 1, "every tile is a terminal or honour"))
        else:
            limit.append(ScoreLine("么九", 10, "every tile is a terminal (pure 1s/9s)"))

    if single_suit is not None and not honors_present and is_chuuren(hand_tiles, single_suit):
        limit.append(ScoreLine("九子連環", 10, "1112345678999 + one more tile, same suit"))

    return regular, limit


def _score_winning_condition(flags: ScoreFlags, hand_concealed: bool, is_strictly_concealed: bool) -> list[ScoreLine]:
    """Faan from how the hand was won, independent of shape. Always stacks, even onto limit hands."""
    lines: list[ScoreLine] = []
    if flags.zimo:
        lines.append(ScoreLine("自摸", 1, "self-drawn win"))
    if hand_concealed and not is_strictly_concealed:
        lines.append(ScoreLine("門前清", 1, "fully concealed hand"))
    if flags.cg:
        lines.append(ScoreLine("搶槓", 1, "robbed another player's added kong"))
    if flags.hoidai:
        lines.append(ScoreLine("海底撈月", 1, "drew the very last tile of the wall"))
    if flags.hodai:
        lines.append(ScoreLine("河底撈魚", 1, "drew the final discarded tile of the round"))
    if flags.gshf:
        lines.append(ScoreLine("槓上開花", 1, "won on a kong replacement tile"))
    if flags.gsg:
        lines.append(ScoreLine("槓上槓", 8, "won on a second consecutive kong replacement tile"))
    if flags.tinwu:
        lines.append(ScoreLine("天糊", 13, "dealer's starting hand was already complete"))
    if flags.deiwu:
        lines.append(ScoreLine("地糊", 13, "won on the dealer's first discard, before any calls"))
    return lines


def _effective_groups(groups: list[Group], winning_tile: str, zimo: bool, hand_concealed: bool) -> list[Group]:
    """
    On ron, a concealed triplet completed by the winning tile doesn't count as
    concealed for 四暗刻 purposes (the classic ankou/shanpon exception) -- unless
    the winning tile instead completed the pair, in which case no triplet here
    matches it and nothing is downgraded. `hand_concealed` (any open meld in the
    hand text makes this false, same as riichi.py's `HandContext.concealed`)
    downgrades every group at once when the hand has an open meld anywhere.
    """
    if not hand_concealed:
        groups = [Group(g.kind, tile=g.tile, suit=g.suit, start=g.start, concealed=False) for g in groups]
    if zimo:
        return groups
    adjusted: list[Group] = []
    downgraded = False
    for g in groups:
        if not downgraded and g.kind in ("triplet", "kan") and g.concealed and g.tile == winning_tile:
            adjusted.append(Group(g.kind, tile=g.tile, concealed=False))
            downgraded = True
        else:
            adjusted.append(g)
    return adjusted


def _score_standard_decomp(
    groups: list[Group],
    pair: str,
    winning_tile: str,
    flags: ScoreFlags,
    hand_concealed: bool,
    generic_regular: list[ScoreLine],
    generic_limit: list[ScoreLine],
) -> tuple[list[ScoreLine], list[ScoreLine], bool]:
    """Returns (hand_tier_lines, wind_dragon_lines, is_strictly_concealed) for one decomposition."""
    triplets = [g for g in groups if g.kind in ("triplet", "kan")]
    kans = [g for g in groups if g.kind == "kan"]

    regular = list(generic_regular)
    limit = list(generic_limit)

    if not triplets:
        regular.append(ScoreLine("平糊", 1, "every group is a chow"))
    if len(triplets) == 4:
        regular.append(ScoreLine("對對糊", 3, "every group is a pung/kong"))

    dragon_triplets = [g for g in triplets if is_dragon(g.tile)]
    if len(dragon_triplets) == 2 and is_dragon(pair):
        regular.append(ScoreLine("小三元", 3, "two dragon triplets + dragon pair"))
    elif len(dragon_triplets) == 3:
        regular.append(ScoreLine("大三元", 5, "three dragon triplets"))

    wind_triplets = [g for g in triplets if is_wind(g.tile)]
    if len(wind_triplets) == 3 and is_wind(pair):
        regular.append(ScoreLine("小四喜", 6, "three wind triplets + the fourth wind as pair"))
    elif len(wind_triplets) == 4:
        limit.append(ScoreLine("大四喜", 13, "all four winds as triplets"))

    if len(kans) == 4:
        limit.append(ScoreLine("十八羅漢", 13, "four kongs"))

    eff_groups = _effective_groups(groups, winning_tile, flags.zimo, hand_concealed)
    concealed_triplets = [g for g in eff_groups if g.kind in ("triplet", "kan") and g.concealed]
    if len(concealed_triplets) == 4:
        limit.append(ScoreLine("四暗刻", 10, "four concealed pungs/kongs"))

    is_strictly_concealed = any(line.name in _INHERENTLY_CONCEALED for line in limit)

    if limit:
        return [max(limit, key=lambda line: line.points)], [], is_strictly_concealed

    wind_dragon: list[ScoreLine] = []
    for g in triplets:
        if is_wind(g.tile):
            if g.tile == flags.seat_wind:
                wind_dragon.append(ScoreLine("門風", 1, f"{g.tile} triplet matches seat wind"))
            if g.tile == flags.round_wind:
                wind_dragon.append(ScoreLine("圈風", 1, f"{g.tile} triplet matches round wind"))
        elif is_dragon(g.tile):
            match g.tile:
                case "middle":  # red 中
                    wind_dragon.append(ScoreLine("紅中", 1, f"{g.tile} triplet"))
                case "faat":  # green 發
                    wind_dragon.append(ScoreLine("發財", 1, f"{g.tile} triplet"))
                case "white":  # white 白
                    wind_dragon.append(ScoreLine("白板", 1, f"{g.tile} triplet"))

    return regular, wind_dragon, is_strictly_concealed


class HongKongRuleset(Ruleset):
    name = "hongkong"

    def compute(
        self,
        text: str,
        seat_wind: str = "east",
        round_wind: str = "east",
        zimo: bool = False,
        min_faan: int = 0,
        cg: bool = False,
        hoidai: bool = False,
        hodai: bool = False,
        gshf: bool = False,
        gsg: bool = False,
        tinwu: bool = False,
        deiwu: bool = False,
    ) -> ScoreResult:
        flags = ScoreFlags(
            seat_wind=seat_wind,
            round_wind=round_wind,
            zimo=zimo,
            min_faan=min_faan,
            cg=cg,
            hoidai=hoidai,
            hodai=hodai,
            gshf=gshf,
            gsg=gsg,
            tinwu=tinwu,
            deiwu=deiwu,
        )

        hctx = build_context(text)
        hand_tiles = hctx.all_tiles
        winning_tile = hctx.winning_tile
        # Whether the hand is open (has a called chi/pon/minkan) is read straight off the
        # `[...]`/`(...)` meld notation, same as riichi.py -- no separate open/concealed flag.
        hand_concealed = hctx.concealed

        generic_regular, generic_limit = _score_generic(hand_tiles)
        if not hand_concealed:
            generic_limit = [line for line in generic_limit if line.name != "九子連環"]

        shape_candidates: list[tuple[str, list[ScoreLine]]] = []

        if not hctx.melds and is_seven_pairs(hand_tiles):
            regular = [*generic_regular, ScoreLine("七對子", 4, "seven distinct pairs")]
            hand_tier = [max(generic_limit, key=lambda line: line.points)] if generic_limit else regular
            win_cond = _score_winning_condition(flags, hand_concealed, is_strictly_concealed=True)
            shape_candidates.append(("seven_pairs", [*hand_tier, *win_cond]))

        if not hctx.melds and is_thirteen_orphans(hand_tiles):
            win_cond = _score_winning_condition(flags, hand_concealed, is_strictly_concealed=True)
            shape_candidates.append(("thirteen_orphans", [ScoreLine("十三么", 13, "thirteen orphans"), *win_cond]))

        for decomp in decompose_hand(hctx.concealed_tiles, num_groups=4 - len(hctx.melds)):
            groups = [*decomp["groups"], *hctx.melds]
            pair = decomp["pair"]
            hand_tier, wind_dragon, is_strictly_concealed = _score_standard_decomp(
                groups,
                pair,
                winning_tile,
                flags,
                hand_concealed,
                generic_regular,
                generic_limit,
            )
            win_cond = _score_winning_condition(flags, hand_concealed, is_strictly_concealed)
            shape_candidates.append(("standard", [*hand_tier, *wind_dragon, *win_cond]))

        if not shape_candidates:
            raise ScoringError(
                "Not a valid complete hand: doesn't break down into four sets + a pair, "
                "isn't seven pairs and isn't thirteen orphans.",
            )

        best_shape, best_lines, best_total = None, None, None
        for shape, lines in shape_candidates:
            total = min(MAX_FAAN, sum(line.points for line in lines))
            if best_total is None or total > best_total:
                best_shape, best_lines, best_total = shape, lines, total

        if best_total == 0:
            raise ScoringError("No matching 役 at all (雞糊, a chicken hand) -- this can't win.")
        if best_total < flags.min_faan:
            raise ScoringError(f"Only {best_total} faan, below the {flags.min_faan}-faan minimum to win (雞糊).")

        return ScoreResult(
            shape=best_shape,
            hand_tiles=hand_tiles,
            winning_tile=winning_tile,
            lines=best_lines,
            total=best_total,
            points=_points_for(best_total, flags.zimo),
        )
