"""
Riichi (Japanese) mahjong scoring engine, per [riichi.md](riichi.md)
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import cast

from modules.Mahjong.hand import ORPHAN_KINDS, Group, decompose_hand, is_seven_pairs, is_thirteen_orphans
from modules.Mahjong.tiles import (
    DRAGONS,
    SUITS,
    WINDS,
    is_dragon,
    is_honor,
    is_simple,
    is_terminal,
    is_wind,
    number_of,
    suit_of,
)
from modules.Mahjong.waits import classify_waits, is_chuuren, is_chuuren_9_wait, is_kokushi_13_wait

from .base import Ruleset, ScoreLine, ScoringError
from .context import HandContext, build_context

_GREEN_TILES: set[str] = {f"{n}sak" for n in (2, 3, 4, 6, 8)} | {"faat"}

# (non_dealer_ron, non_dealer_tsumo_from_nondealer, non_dealer_tsumo_from_dealer, dealer_ron, dealer_tsumo_each)
# 親/子
_LIMIT_BASE: dict[str, tuple[int, int, int, int, int]] = {
    "満貫": (8000, 2000, 4000, 12000, 4000),
    "跳満": (12000, 3000, 6000, 18000, 6000),
    "倍満": (16000, 4000, 8000, 24000, 8000),
    "三倍満": (24000, 6000, 12000, 36000, 12000),
    "数え役満": (32000, 8000, 16000, 48000, 16000),
}
_LIMIT_BRACKETS: list[tuple[int, int, str]] = [
    (5, 5, "満貫"),
    (6, 7, "跳満"),
    (8, 10, "倍満"),
    (11, 12, "三倍満"),
    (13, 10**9, "数え役満"),
]
_YAKUMAN_MULTIPLIER_NAMES: dict[int, str] = {
    1: "役満",
    2: "二倍役満",
    3: "三倍役満",
    4: "四倍役満",
    5: "五倍役満",
    6: "六倍役満",
}

YAKU_HELP_URL = "https://mahjongcalculators.com/yaku/{}"


def yaku_link(yaku_name: str) -> str:
    """Return a URL to the yaku's page on mahjongcalculators.com"""
    return YAKU_HELP_URL.format(yaku_name.replace(" ", "-").replace("'", "").lower())


@dataclass
class RiichiFlags:
    seat_wind: str = "east"
    round_wind: str = "east"
    tsumo: bool = False
    riichi: bool = False
    double_riichi: bool = False
    ippatsu: bool = False
    haitei: bool = False
    houtei: bool = False
    rinshan: bool = False
    chankan: bool = False
    renhou: bool = False
    tenhou: bool = False
    chiihou: bool = False
    honba: int = 0
    dora_indicators: list[str] = field(default_factory=list)
    uradora: bool = False
    akadora: int = 0

    def __post_init__(self):
        if self.seat_wind not in WINDS:
            # if a single letter is given, try to map it to a wind
            if len(self.seat_wind) == 1 and self.seat_wind.lower() in "eswn":
                match self.seat_wind.lower():
                    case "e":
                        self.seat_wind = "east"
                    case "s":
                        self.seat_wind = "south"
                    case "w":
                        self.seat_wind = "west"
                    case "n":
                        self.seat_wind = "north"
                    case _:
                        raise ScoringError(f"`{self.seat_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
            else:
                raise ScoringError(f"`{self.seat_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
        if self.round_wind not in WINDS:
            # if a single letter is given, try to map it to a wind
            if len(self.round_wind) == 1 and self.round_wind.lower() in "eswn":
                match self.round_wind.lower():
                    case "e":
                        self.round_wind = "east"
                    case "s":
                        self.round_wind = "south"
                    case "w":
                        self.round_wind = "west"
                    case "n":
                        self.round_wind = "north"
                    case _:
                        raise ScoringError(f"`{self.round_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
            else:
                raise ScoringError(f"`{self.round_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
        if self.honba < 0:
            raise ScoringError("honba can't be negative.")
        if self.uradora and not (self.riichi or self.double_riichi):
            raise ScoringError("uradora requires riichi (or double riichi) to also be set.")
        if self.uradora and not self.dora_indicators:
            raise ScoringError("uradora requires dora indicators to also be given.")
        if self.akadora < 0:
            raise ScoringError("akadora can't be negative.")

    @property
    def is_dealer(self) -> bool:
        return self.seat_wind == "east"


@dataclass
class RiichiScoreResult:
    shape: str
    han: int | None
    fu: int | None
    lines: list[ScoreLine]
    is_yakuman: bool
    limit_name: str | None
    payments: dict[str, int]
    total_points: int
    hand_tiles: list[str]
    winning_tile: str


def _dora_tile(indicator: str) -> str:
    suit = suit_of(indicator)
    if suit is not None:
        n = number_of(indicator)
        return f"{n % 9 + 1}{suit}"
    if indicator in WINDS:
        return WINDS[(WINDS.index(indicator) + 1) % 4]
    if indicator in DRAGONS:
        return DRAGONS[(DRAGONS.index(indicator) + 1) % 3]
    raise ScoringError(f"`{indicator}` isn't a valid dora indicator.")


def _round100(x: int) -> int:
    return -(-x // 100) * 100


def _build_payments(is_dealer: bool, tsumo: bool, values: tuple[int, int, int, int, int], honba: int) -> dict[str, int]:
    """Calculate payments

    The base formula is:
        - Ron: 1x base for 子, 3x base for 親
        - Tsumo: 1x base from each 子, 2x base from 親 for 子 tsumo
                 2x base from each 子 for 親 tsumo
    """
    non_dealer_ron, nd_tsumo_each, nd_tsumo_dealer, dealer_ron, dealer_tsumo_each = values
    if not tsumo:
        base = dealer_ron if is_dealer else non_dealer_ron
        return {"ron": _round100(base) + 300 * honba}
    if is_dealer:
        return {"tsumo_each": _round100(dealer_tsumo_each) + 100 * honba}
    return {
        "tsumo_each": _round100(nd_tsumo_each) + 100 * honba,
        "tsumo_dealer": _round100(nd_tsumo_dealer) + 100 * honba,
    }


def _limit_name(han: int) -> str:
    for lo, hi, name in _LIMIT_BRACKETS:
        if lo <= han <= hi:
            return name
    return "数え役満"


def _points_for(han: int, fu: int) -> tuple[str | None, tuple[int, int, int, int, int]]:
    base = fu * (2 ** (han + 2))
    if han >= 5 or base >= 2000:
        name = _limit_name(max(han, 5))
        return name, _LIMIT_BASE[name]
    return None, (base * 4, base * 1, base * 2, base * 6, base * 2)


def describe_yakuman(multiplier: int) -> str:
    return _YAKUMAN_MULTIPLIER_NAMES.get(multiplier, f"{multiplier}倍役満")


def _touches_terminal_or_honor(group: Group) -> bool:
    if group.kind in ("triplet", "kan"):
        tile = cast("str", group.tile)
        return is_terminal(tile) or is_honor(tile)
    return group.start in (1, 7)  # sequence starting at 1 or 7 includes a 1 or a 9


def _effective_groups(groups: list[Group], wait: str, winning_tile: str, tsumo: bool) -> list[Group]:
    """
    Apply the shanpon-ron rule: the triplet completed via ron on a shanpon
    wait counts as open for fu/sanankou/suuankou purposes, even though the
    rest of the hand may otherwise be concealed.
    """
    if tsumo or wait != "shanpon":
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


def _compute_fu(
    eff_groups: list[Group],
    pair: str,
    flags: RiichiFlags,
    wait: str,
    is_pinfu: bool,
    hand_concealed: bool,
) -> int:
    if is_pinfu:
        return 20 if flags.tsumo else 30

    fu = 20
    if flags.tsumo:
        fu += 2
    elif hand_concealed:
        fu += 10

    if wait in ("kanchan", "penchan", "tanki"):
        fu += 2

    if is_dragon(pair) or pair in (flags.seat_wind, flags.round_wind):
        fu += 4 if (pair == flags.seat_wind and pair == flags.round_wind) else 2

    for g in eff_groups:
        if g.kind == "sequence":
            continue
        tile = cast("str", g.tile)
        is_term = is_terminal(tile) or is_honor(tile)
        if g.kind == "kan":
            fu += (32 if is_term else 16) if g.concealed else (16 if is_term else 8)
        else:
            fu += (8 if is_term else 4) if g.concealed else (4 if is_term else 2)

    fu = -(-fu // 10) * 10
    if not flags.tsumo and not hand_concealed and fu < 30:
        fu = 30
    return fu


def _score_bonus(hctx: HandContext, flags: RiichiFlags) -> list[ScoreLine]:
    lines: list[ScoreLine] = []
    if flags.ippatsu:
        lines.append(ScoreLine("一発", 1, "won within one go-around of declaring riichi, no calls in between"))

    dora_count = sum(hctx.all_tiles.count(_dora_tile(ind)) for ind in flags.dora_indicators)
    if dora_count:
        lines.append(ScoreLine("ドラ", dora_count, f"{dora_count}x"))

    if flags.uradora and dora_count:
        lines.append(ScoreLine("裏ドラ", dora_count, f"{dora_count}x"))

    if flags.akadora:
        lines.append(ScoreLine("赤ドラ", flags.akadora, f"{flags.akadora}x"))

    return lines


def _validate_situational(hctx: HandContext, flags: RiichiFlags) -> None:
    if (flags.riichi or flags.double_riichi or flags.ippatsu) and not hctx.concealed:
        raise ScoringError("Riichi/ippatsu require a fully concealed hand.")
    if flags.ippatsu and not (flags.riichi or flags.double_riichi):
        raise ScoringError("Ippatsu requires `--riichi` (or `--double` for double riichi) to also be set.")
    if (flags.haitei or flags.rinshan) and not flags.tsumo:
        raise ScoringError("Haitei/rinshan are self-draw (tsumo) wins, thus require `--tsumo` to be also set.")
    if (flags.houtei or flags.chankan) and flags.tsumo:
        raise ScoringError("Houtei/chankan are ron wins, not tsumo.")
    if flags.tenhou and not (flags.tsumo and flags.is_dealer):
        raise ScoringError("Tenhou requires being the dealer (親) and winning by tsumo.")
    if flags.chiihou and not (flags.tsumo and not flags.is_dealer):
        raise ScoringError("Chiihou requires being a non-dealer (子) and winning by tsumo.")


def _score_chiitoitsu(hctx: HandContext, flags: RiichiFlags) -> tuple[list[ScoreLine], list[ScoreLine]]:
    lines = [ScoreLine(f"[七対子]({yaku_link('chiitoitsu')})", 2, "seven distinct pairs")]
    yakuman_lines: list[ScoreLine] = []

    all_tiles = hctx.all_tiles
    no_honors = not any(is_honor(t) for t in all_tiles)
    suits_present = {suit_of(t) for t in all_tiles if suit_of(t)}
    single_suit = next(iter(suits_present)) if len(suits_present) == 1 else None

    if all(is_honor(t) for t in all_tiles):
        yakuman_lines.append(
            ScoreLine(f"[字一色]({yaku_link('tsuiisou')})", 1, "every tile is an honour tile (chiitoitsu shape)")
        )

    if flags.double_riichi:
        lines.append(ScoreLine(f"[ダブル立直]({yaku_link('double riichi')})", 2, "double riichi"))
    elif flags.riichi:
        lines.append(ScoreLine(f"[立直]({yaku_link('riichi')})", 1, "riichi"))
    if flags.tsumo:
        lines.append(ScoreLine(f"[門前清自摸和]({yaku_link('tsumo')})", 1, "tsumo"))
    if all(is_simple(t) for t in all_tiles):
        lines.append(ScoreLine(f"[断幺九]({yaku_link('tanyao')})", 1, "tankou; all simples"))
    if single_suit and not no_honors:
        lines.append(ScoreLine(f"[混一色]({yaku_link('honitsu')})", 3, "one suit + honours"))
    elif single_suit and no_honors:
        lines.append(ScoreLine(f"[清一色]({yaku_link('chinitsu')})", 6, "pure one suit"))
    if all(is_terminal(t) or is_honor(t) for t in all_tiles) and not no_honors:
        lines.append(ScoreLine(f"混老頭", 2, "every tile is 1/9 or honour"))
    if flags.haitei:
        lines.append(ScoreLine(f"[海底摸月]({yaku_link('haitei')})", 1, "drew the last tile in the wall"))
    if flags.houtei:
        lines.append(ScoreLine(f"[河底撈魚]({yaku_link('houtei')})", 1, "ronned the last discard"))
    if flags.tenhou:
        yakuman_lines.append(ScoreLine("天和", 1, "dealer's starting hand was already complete"))
    if flags.chiihou:
        yakuman_lines.append(ScoreLine("地和", 1, "won on the first draw, before any calls"))

    return lines, yakuman_lines


def _score_kokushi(hctx: HandContext, flags: RiichiFlags) -> tuple[list[ScoreLine], list[ScoreLine]]:
    hand_minus_winning = list(hctx.all_tiles)
    hand_minus_winning.remove(hctx.winning_tile)
    if is_kokushi_13_wait(hand_minus_winning, ORPHAN_KINDS):
        yakuman_lines = [ScoreLine(f"[国士無双十三面]({yaku_link('kokushi')})", 2, "thirteen-sided wait kokushi musou")]
    else:
        yakuman_lines = [ScoreLine(f"[国士無双]({yaku_link('kokushi')})", 1, "thirteen orphans")]
    if flags.tenhou:
        yakuman_lines.append(ScoreLine("天和", 1, "dealer's starting hand was already complete"))
    if flags.chiihou:
        yakuman_lines.append(ScoreLine("地和", 1, "won on the first draw, before any calls"))
    return [], yakuman_lines


def _score_standard(
    hctx: HandContext,
    groups: list[Group],
    pair: str,
    flags: RiichiFlags,
    wait: str,
) -> tuple[list[ScoreLine], list[ScoreLine], int]:
    lines: list[ScoreLine] = []
    yakuman_lines: list[ScoreLine] = []

    eff_groups = _effective_groups(groups, wait, hctx.winning_tile, flags.tsumo)
    triplets = [g for g in eff_groups if g.kind in ("triplet", "kan")]
    sequences = [g for g in eff_groups if g.kind == "sequence"]
    kans = [g for g in eff_groups if g.kind == "kan"]
    concealed_triplets = [g for g in triplets if g.concealed]

    all_tiles = hctx.all_tiles
    no_honors = not any(is_honor(t) for t in all_tiles)
    suits_present = {suit_of(t) for t in all_tiles if suit_of(t)}
    single_suit = next(iter(suits_present)) if len(suits_present) == 1 else None

    # `triplets` is already filtered to kind in ("triplet", "kan"), which always set `tile`.
    wind_triplets = [g for g in triplets if is_wind(cast("str", g.tile))]
    dragon_triplets = [g for g in triplets if is_dragon(cast("str", g.tile))]

    # --- yakuman shapes ---
    if len(dragon_triplets) == 3:
        yakuman_lines.append(ScoreLine(f"[大三元]({yaku_link('daisangen')})", 1, "three dragon triplets"))
    if len(wind_triplets) == 4:
        yakuman_lines.append(ScoreLine(f"[大四喜]({yaku_link('daisuushii')})", 2, "all four winds as triplets"))
    elif len(wind_triplets) == 3 and is_wind(pair):
        yakuman_lines.append(
            ScoreLine(f"[小四喜]({yaku_link('shousuushii')})", 1, "three wind triplets + the fourth wind as pair")
        )
    if all(is_terminal(t) for t in all_tiles):
        yakuman_lines.append(
            ScoreLine(f"[清老頭]({yaku_link('chinroutou')})", 1, "every tile is a terminal, no honours")
        )
    if all(is_honor(t) for t in all_tiles):
        yakuman_lines.append(ScoreLine(f"[字一色]({yaku_link('tsuiisou')})", 1, "every tile is an honour"))
    if all(t in _GREEN_TILES for t in all_tiles):
        yakuman_lines.append(ScoreLine(f"[緑一色]({yaku_link('ryuuiisou')})", 1, "green tiles only"))
    if len(kans) == 4:
        yakuman_lines.append(ScoreLine("四槓子", 1, "four kans/quadruplets"))
    if len(concealed_triplets) == 4:
        if wait == "tanki":
            yakuman_lines.append(
                ScoreLine(f"[四暗刻単騎]({yaku_link('suuankou')})", 2, "four concealed triplets, tanki wait")
            )
        else:
            yakuman_lines.append(ScoreLine(f"[四暗刻]({yaku_link('suuankou')})", 1, "four concealed triplets"))
    if single_suit and no_honors and is_chuuren(all_tiles, single_suit):
        hand_minus_winning = list(all_tiles)
        hand_minus_winning.remove(hctx.winning_tile)
        if is_chuuren_9_wait(hand_minus_winning, single_suit):
            yakuman_lines.append(
                ScoreLine(f"[純正九蓮宝燈]({yaku_link('chuuren-poutou')})", 2, "nine-sided wait pure nine gates")
            )
        else:
            yakuman_lines.append(ScoreLine(f"[九蓮宝燈]({yaku_link('chuuren-poutou')})", 1, "pure nine gates"))
    if flags.tenhou:
        yakuman_lines.append(ScoreLine("天和", 1, "dealer's starting hand was already complete"))
    if flags.chiihou:
        yakuman_lines.append(ScoreLine("地和", 1, "won on the first draw, before any calls"))

    # --- 1-han ---
    if flags.double_riichi:
        lines.append(ScoreLine(f"[ダブル立直]({yaku_link('double riichi')})", 2, "double riichi"))
    elif flags.riichi:
        lines.append(ScoreLine(f"[立直]({yaku_link('riichi')})", 1, "riichi"))
    if hctx.concealed and flags.tsumo:
        lines.append(ScoreLine(f"[門前清自摸和]({yaku_link('tsumo')})", 1, "tsumo"))
    for g in triplets:
        if is_dragon(cast("str", g.tile)):
            lines.append(ScoreLine("役牌", 1, f"{g.tile} triplet"))
        elif is_wind(cast("str", g.tile)):
            match_seat = g.tile == flags.seat_wind
            match_round = g.tile == flags.round_wind
            if match_seat and match_round:
                lines.append(ScoreLine("役牌", 2, f"{g.tile} triplet matches both seat and round wind"))
            elif match_seat or match_round:
                lines.append(ScoreLine("自風", 1, f"{g.tile} triplet matches wind"))
    if all(is_simple(t) for t in all_tiles):
        lines.append(ScoreLine(f"[断幺九]({yaku_link('tanyao')})", 1, "all simples"))

    is_pinfu = (
        hctx.concealed
        and not triplets
        and not is_dragon(pair)
        and pair != flags.seat_wind
        and pair != flags.round_wind
        and wait == "ryanmen"
    )
    if is_pinfu:
        lines.append(
            ScoreLine(f"[平和]({yaku_link('pinfu')})", 1, "pinfu; all sequences, non-yakuhai pair, two-sided wait")
        )

    seq_key_counts = Counter((g.suit, g.start) for g in sequences)
    dup_pairs = sum(c // 2 for c in seq_key_counts.values())
    if hctx.concealed and dup_pairs >= 2:
        lines.append(ScoreLine(f"[二盃口]({yaku_link('ryanpeikou')})", 3, "two pairs of identical sequences"))
    elif hctx.concealed and dup_pairs == 1:
        lines.append(ScoreLine(f"[一盃口]({yaku_link('iipeikou')})", 1, "one pair of identical sequences"))

    if flags.haitei:
        lines.append(ScoreLine(f"[海底摸月]({yaku_link('haitei')})", 1, "drew the last tile in the wall"))
    if flags.houtei:
        lines.append(ScoreLine(f"[河底撈魚]({yaku_link('houtei')})", 1, "ronned the last discard"))
    if flags.rinshan:
        lines.append(ScoreLine(f"[嶺上開花]({yaku_link('rinshan')})", 1, "drew off a kan replacement tile"))
    if flags.chankan:
        lines.append(ScoreLine(f"[槍槓]({yaku_link('chankan')})", 1, "robbed another player's added kan"))

    # --- 2-han ---
    lines.extend(
        ScoreLine(f"[一気通貫]({yaku_link('ittsu')})", 2 if hctx.concealed else 1, f"{suit} runs 1-9")
        for suit in SUITS
        if all(any(g.matches("sequence", suit=suit, start=s) for g in sequences) for s in (1, 4, 7))
    )

    starts: dict[int, set[str]] = {}
    for g in sequences:
        starts.setdefault(cast("int", g.start), set()).add(cast("str", g.suit))
    if any(len(s) == 3 for s in starts.values()):
        lines.append(
            ScoreLine(
                f"[三色同順]({yaku_link('sanshoku doukou')})",
                2 if hctx.concealed else 1,
                "same-numbered run in all three suits",
            )
        )

    touches = all(_touches_terminal_or_honor(g) for g in eff_groups) and (is_terminal(pair) or is_honor(pair))
    if touches:
        if no_honors:
            lines.append(
                ScoreLine(
                    f"[純全帯幺九]({yaku_link('junchan')})",
                    3 if hctx.concealed else 2,
                    "every group + pair touches a terminal, no honours",
                )
            )
        else:
            lines.append(
                ScoreLine(f"混全帯幺九", 2 if hctx.concealed else 1, "every group + pair touches a terminal or honour")
            )

    if all(is_terminal(t) or is_honor(t) for t in all_tiles) and not no_honors:
        lines.append(ScoreLine(f"混老頭", 2, "every tile is a terminal or honour"))

    if len(dragon_triplets) == 2 and is_dragon(pair):
        lines.append(ScoreLine(f"[小三元]({yaku_link('shosangen')})", 2, "two dragon triplets + dragon pair"))

    if len(triplets) == 4:
        lines.append(ScoreLine(f"[対々和]({yaku_link('toitoi')})", 2, "all four groups are triplets"))

    if len(concealed_triplets) == 3:
        lines.append(ScoreLine(f"[三暗刻]({yaku_link('sanankou')})", 2, "three concealed triplets"))

    if len(kans) == 3:
        lines.append(ScoreLine("三槓子", 2, "three kans"))

    trip_by_number: dict[int, set[str]] = {}
    for g in triplets:
        tile = cast("str", g.tile)
        s = suit_of(tile)
        if s:
            trip_by_number.setdefault(cast("int", number_of(tile)), set()).add(s)
    if any(len(s) == 3 for s in trip_by_number.values()):
        lines.append(
            ScoreLine(f"[三色同刻]({yaku_link('sanshoku doukou')})", 2, "same-numbered triplet in all three suits")
        )

    # --- 3/6-han ---
    if single_suit and not no_honors:
        lines.append(ScoreLine(f"[混一色]({yaku_link('honitsu')})", 3 if hctx.concealed else 2, "one suit + honours"))
    elif single_suit and no_honors:
        lines.append(ScoreLine(f"[清一色]({yaku_link('chinitsu')})", 6 if hctx.concealed else 5, "pure one suit"))

    fu = _compute_fu(eff_groups, pair, flags, wait, is_pinfu, hctx.concealed)
    return lines, yakuman_lines, fu


class RiichiRuleset(Ruleset):
    name = "riichi"

    def compute(self, text: str, **flags_kwargs) -> RiichiScoreResult:
        flags = RiichiFlags(**flags_kwargs)

        if flags.renhou:
            return self._compute_renhou(text, flags)

        hctx = build_context(text)
        _validate_situational(hctx, flags)

        shape_candidates: list[tuple[str, int, list[ScoreLine], list[ScoreLine]]] = []

        if not hctx.melds and is_seven_pairs(hctx.all_tiles):
            lines, yakuman_lines = _score_chiitoitsu(hctx, flags)
            shape_candidates.append(("chiitoitsu", 25, lines, yakuman_lines))

        if not hctx.melds and is_thirteen_orphans(hctx.all_tiles):
            lines, yakuman_lines = _score_kokushi(hctx, flags)
            shape_candidates.append(("kokushi", 0, lines, yakuman_lines))

        for decomp in decompose_hand(hctx.concealed_tiles, num_groups=4 - len(hctx.melds)):
            groups = [*decomp["groups"], *hctx.melds]
            pair = decomp["pair"]
            try:
                waits = classify_waits({"pair": pair, "groups": groups}, hctx.winning_tile)
            except ValueError:
                continue
            for wait in waits:
                lines, yakuman_lines, fu = _score_standard(hctx, groups, pair, flags, wait)
                shape_candidates.append(("standard", fu, lines, yakuman_lines))

        if not shape_candidates:
            raise ScoringError(
                "Not a valid complete hand: doesn't break down into four sets + a pair, "
                "isn't seven pairs and isn't thirteen orphans.",
            )

        best: RiichiScoreResult | None = None
        last_error: ScoringError | None = None
        for shape, fu, lines, yakuman_lines in shape_candidates:
            try:
                result = self._finalise(shape, fu, lines, yakuman_lines, flags, hctx)
            except ScoringError as e:
                last_error = e
                continue
            if best is None or result.total_points > best.total_points:
                best = result

        if best is None:
            raise last_error or ScoringError("No yaku for this hand (dora/fu alone can't win).")
        return best

    def _finalise(
        self,
        shape: str,
        fu: int,
        lines: list[ScoreLine],
        yakuman_lines: list[ScoreLine],
        flags: RiichiFlags,
        hctx: HandContext,
    ) -> RiichiScoreResult:
        if yakuman_lines:
            multiplier = sum(line.points for line in yakuman_lines)
            values = tuple(v * multiplier for v in _LIMIT_BASE["数え役満"])
            limit_name = describe_yakuman(multiplier)
            payments = _build_payments(flags.is_dealer, flags.tsumo, values, flags.honba)
            return RiichiScoreResult(
                shape=shape,
                han=None,
                fu=None,
                lines=yakuman_lines,
                is_yakuman=True,
                limit_name=limit_name,
                payments=payments,
                total_points=sum(payments.values()),
                hand_tiles=hctx.all_tiles,
                winning_tile=hctx.winning_tile,
            )

        if not lines:
            raise ScoringError(f"No yaku for this {shape} hand (dora alone can't win).")

        all_lines = lines + _score_bonus(hctx, flags)
        han = sum(line.points for line in all_lines)
        limit_name, values = _points_for(han, fu)
        payments = _build_payments(flags.is_dealer, flags.tsumo, values, flags.honba)
        return RiichiScoreResult(
            shape=shape,
            han=han,
            fu=fu,
            lines=all_lines,
            is_yakuman=False,
            limit_name=limit_name,
            payments=payments,
            total_points=sum(payments.values()),
            hand_tiles=hctx.all_tiles,
            winning_tile=hctx.winning_tile,
        )

    def _compute_renhou(self, text: str, flags: RiichiFlags) -> RiichiScoreResult:
        if flags.tsumo:
            raise ScoringError("Renhou (人和) is a ron-only yaku, not a self-draw (tsumo) yaku.")
        if flags.is_dealer:
            raise ScoringError("Renhou (人和) requires being a non-dealer (子).")

        hctx = build_context(text)
        lines = [
            ScoreLine(
                "人和",
                0,
                "non-dealer (子), already tenpai at deal, won by ron before your first draw, first go-around",
            ),
        ]
        payments = _build_payments(False, False, _LIMIT_BASE["満貫"], flags.honba)
        return RiichiScoreResult(
            shape="renhou",
            han=None,
            fu=None,
            lines=lines,
            is_yakuman=False,
            limit_name="満貫",
            payments=payments,
            total_points=sum(payments.values()),
            hand_tiles=hctx.all_tiles,
            winning_tile=hctx.winning_tile,
        )
