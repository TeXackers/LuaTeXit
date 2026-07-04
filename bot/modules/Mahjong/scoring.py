"""
Mahjong scoring engine using 홍콩족보.md i.e. everything derivable from the 14 tiles themselves (+ seat/round wind, concealed-or-open, and tsumo-or-ron), with no dependency on turn order, wall state, or declared-kong history.
"""

from __future__ import annotations

import itertools
from collections import Counter, namedtuple
from dataclasses import dataclass

from .hand import decompose_hand, is_seven_pairs, is_thirteen_orphans
from .tiles import (
    DRAGONS,
    FLOWER_SEAT,
    FLOWERS_PLANT,
    FLOWERS_SEASON,
    SUITS,
    WINDS,
    MahjongParseError,
    is_dragon,
    is_honor,
    is_simple,
    is_terminal,
    is_wind,
    number_of,
    parse_hand,
    split_flowers,
    suit_of,
)
from .waits import is_shanpon, is_tanki

ScoreLine = namedtuple("ScoreLine", "name points note")


class ScoringError(ValueError):
    """Raised when the given tiles don't form a valid, scoreable winning hand."""


@dataclass
class ScoreFlags:
    seat_wind: str = "east"
    round_wind: str = "east"
    concealed: bool = True
    tsumo: bool = False

    def __post_init__(self):
        if self.seat_wind not in WINDS:
            raise ScoringError(f"`{self.seat_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")
        if self.round_wind not in WINDS:
            raise ScoringError(f"`{self.round_wind}` isn't a wind (must be one of {', '.join(WINDS)}).")


@dataclass
class ScoreResult:
    shape: str
    hand_tiles: list[str]
    flower_tiles: list[str]
    winning_tile: str
    lines: list[ScoreLine]
    total: int


def _score_flowers(flower_tiles: list[str], flags: ScoreFlags) -> list[ScoreLine]:
    lines: list[ScoreLine] = []
    if not flower_tiles:
        lines.append(ScoreLine("無花", 1, "no flowers held"))
        return lines

    seat_idx = WINDS.index(flags.seat_wind)
    for f in flower_tiles:
        if FLOWER_SEAT[f] == seat_idx:
            lines.append(ScoreLine("正花", 2, f"{f} matches your seat wind"))
        else:
            lines.append(ScoreLine("偏花", 1, f"{f} doesn't match your seat wind"))

    plant_held = [f for f in flower_tiles if f in FLOWERS_PLANT]
    season_held = [f for f in flower_tiles if f in FLOWERS_SEASON]
    if len(flower_tiles) == 8:
        lines.append(ScoreLine("화패 8개", 40, "collected all eight flowers"))
    else:
        if len(plant_held) == 4:
            lines.append(ScoreLine("화패 한 종류 (식물)", 10, "collected all four plant flowers"))
        if len(season_held) == 4:
            lines.append(ScoreLine("화패 한 종류 (계절)", 10, "collected all four season flowers"))
    return lines


def _score_generic(hand_tiles: list[str], flags: ScoreFlags) -> tuple[list[ScoreLine], bool, bool]:
    """Rules derivable from the raw tile multiset, independent of how it's grouped."""
    lines: list[ScoreLine] = []

    no_honors = not any(is_honor(t) for t in hand_tiles)
    honors_present = not no_honors
    suits_present = {suit_of(t) for t in hand_tiles if suit_of(t)}

    if all(is_simple(t) for t in hand_tiles):
        lines.append(ScoreLine("斷幺", 5, "all simples"))

    if len(suits_present) == 1:
        if honors_present:
            lines.append(ScoreLine("混一色", 30, "one suit + honours"))
        else:
            lines.append(ScoreLine("清一色", 80, "pure one suit"))

    if not honors_present and 1 <= len(suits_present) <= 2:
        lines.append(ScoreLine("結一門", 5, "missing at least one whole suit, no honours"))

    if len(suits_present) == 3 and any(is_wind(t) for t in hand_tiles) and any(is_dragon(t) for t in hand_tiles):
        lines.append(ScoreLine("三門齊", 10, "all three suits + winds + dragons"))

    if all(is_terminal(t) or is_honor(t) for t in hand_tiles):
        if honors_present:
            lines.append(ScoreLine("混么九", 40, "every tile is a terminal or honour"))
        else:
            lines.append(ScoreLine("清么九", 80, "every tile is a terminal (pure 1s/9s)"))

    return lines, no_honors


def _score_no_honor_family(no_honors: bool, no_flowers: bool, is_pinfu_shape: bool) -> list[ScoreLine]:
    if no_honors and no_flowers and is_pinfu_shape:
        return [ScoreLine("無字花平和", 15, "no honours, no flowers, all-sequence 平糊 shape")]
    if no_honors and no_flowers:
        return [ScoreLine("無字花", 5, "no honours and no flowers")]
    if no_honors:
        return [ScoreLine("無字", 1, "no honour tiles")]
    return []


def _score_concealed_tsumo(flags: ScoreFlags) -> list[ScoreLine]:
    if flags.concealed and flags.tsumo:
        return [ScoreLine("門前清自摸", 5, "concealed & 自摸")]
    if flags.concealed:
        return [ScoreLine("門前清", 3, "fully concealed")]
    if flags.tsumo:
        return [ScoreLine("自摸", 1, "won by self-draw")]
    return []


def _chicken_duck(lines: list[ScoreLine], flags: ScoreFlags) -> list[ScoreLine]:
    excluded = {
        "無花",
        "偏花",
        "正花",
        "화패 8개",
        "화패 한 종류 (식물)",
        "화패 한 종류 (계절)",
        "門前清",
        "自摸",
        "門前清自摸",
    }
    subtotal = sum(line.points for line in lines if line.name not in excluded)
    if subtotal > 0:
        return []
    if flags.tsumo:
        return [ScoreLine("오리", 10, "no other yaku, won by self-draw")]
    return [ScoreLine("닭", 20, "no other yaku")]


def _score_standard(
    decomp: dict,
    flags: ScoreFlags,
    winning_tile: str,
    no_honors: bool,
    no_flowers: bool,
):
    lines: list[ScoreLine] = []
    groups = decomp["groups"]
    pair = decomp["pair"]
    triplets = [g for g in groups if g[0] == "triplet"]
    sequences = [g for g in groups if g[0] == "sequence"]

    is_pinfu_shape = not triplets and not is_honor(pair)
    lines += _score_no_honor_family(no_honors, no_flowers, is_pinfu_shape)

    # 4/5: winds
    for g in triplets:
        tile = g[1]
        if is_wind(tile):
            match_seat = tile == flags.seat_wind
            match_round = tile == flags.round_wind
            if match_seat or match_round:
                pts = 4 if (match_seat and match_round) else 2
                lines.append(ScoreLine("對家碰", pts, f"{tile} triplet matches wind"))
            else:
                lines.append(ScoreLine("碰", 1, f"{tile} triplet (off-wind)"))

    # 6: dragons
    dragon_triplets = [g for g in triplets if is_dragon(g[1])]
    for g in dragon_triplets:
        lines.append(ScoreLine("三元牌", 2, f"{g[1]} triplet"))
    if len(dragon_triplets) == 2 and is_dragon(pair):
        lines.append(ScoreLine("小三元", 20, "two 元 triplets + 元 pair"))
    elif len(dragon_triplets) == 3:
        lines.append(ScoreLine("大三元", 40, "three 元 triplets"))

    # 46/47: winds as a family
    wind_triplets = [g for g in triplets if is_wind(g[1])]
    if len(wind_triplets) == 4:
        lines.append(ScoreLine("大四喜", 80, "all four 風 as triplets"))
    elif len(wind_triplets) == 3:
        if is_wind(pair):
            lines.append(ScoreLine("小四喜", 60, "three 風 triplets + the fourth wind as pair"))
        else:
            lines.append(ScoreLine("大三風", 30, "three 風 triplets"))
    elif len(wind_triplets) == 2 and is_wind(pair):
        lines.append(ScoreLine("小三風", 15, "two 風 triplets + a 風 pair"))

    # 14: 장안
    if number_of(pair) in (2, 5, 8):
        lines.append(ScoreLine("將眼", 1, f"pair is {pair}"))

    # 11: 대퐁 (shanpon wait, ron only)
    # if not flags.tsumo and is_shanpon(decomp, winning_tile):
    #     lines.append(ScoreLine("大碰", 1, "shanpon wait, won by ron"))

    # # 44: 전구인 (all-open + tanki wait)
    # if not flags.concealed and is_tanki(decomp, winning_tile):
    #     pts = 8 if flags.tsumo else 15
    #     lines.append(ScoreLine("全求人", pts, "fully open, tanki wait"))

    # 23: concealed-triplet count (안커)
    if flags.concealed:
        n = len(triplets)
        if n == 2:
            lines.append(ScoreLine("兩暗刻", 3, "two concealed triplets"))
        elif n == 3:
            lines.append(ScoreLine("三暗刻", 10, "three concealed triplets"))
        elif n == 4:
            lines.append(ScoreLine("四暗刻", 30, "four concealed triplets"))

    # 43: 대대화
    if len(triplets) == 4:
        lines.append(ScoreLine("對對糊", 30, "all four groups are triplets"))

    # 26: 이페커/삼페커/사페커
    seq_counts = Counter(sequences)
    for key, c in seq_counts.items():
        if c == 2:
            lines.append(ScoreLine("兩盃口", 3, f"duplicate {key[1]}-{key[2]} sequence"))
        elif c == 3:
            lines.append(ScoreLine("三盃口", 15, f"tripled {key[1]}-{key[2]} sequence"))
        elif c == 4:
            lines.append(ScoreLine("四盃口", 30, f"quadrupled {key[1]}-{key[2]} sequence"))

    # 24: 이색동순/삼색동순 (same-start sequence shared across suits)
    starts: dict[int, set[str]] = {}
    for _, suit, start in sequences:
        starts.setdefault(start, set()).add(suit)
    for start, suits_here in starts.items():
        if len(suits_here) == 3:
            lines.append(ScoreLine("三色同順", 10, f"all three 順 run {start}-{start + 2}"))
        elif len(suits_here) == 2:
            lines.append(ScoreLine("二色同順", 2, f"two 順 run {start}-{start + 2}"))

    # 27: 이색동커/소삼동커/대삼동커 (same-number triplets across suits)
    trip_by_number: dict[int, set[str]] = {}
    for _, tile in triplets:
        s = suit_of(tile)
        if s:
            trip_by_number.setdefault(number_of(tile), set()).add(s)
    claimed_numbers: set[int] = set()
    if suit_of(pair):
        pair_num = number_of(pair)
        matching = trip_by_number.get(pair_num, set())
        if len(matching) == 2:
            lines.append(ScoreLine("小三同刻", 10, f"{pair_num} pair + triplets in two other suits"))
            claimed_numbers.add(pair_num)
    for num, suits_here in trip_by_number.items():
        if num in claimed_numbers:
            continue
        if len(suits_here) == 3:
            lines.append(ScoreLine("大三同刻", 15, f"{num} triplet in all three suits"))
        elif len(suits_here) == 2:
            lines.append(ScoreLine("二色同刻", 3, f"{num} triplet in two suits"))

    # 28-30: 연커 family (consecutive same-suit triplets, additive pair-extension bonus)
    trip_nums_by_suit: dict[str, list[int]] = {}
    for _, tile in triplets:
        s = suit_of(tile)
        if s:
            trip_nums_by_suit.setdefault(s, []).append(number_of(tile))

    run_scores = {2: 3, 3: 15, 4: 30}
    ext_scores = {3: 8, 4: 20, 5: 40}
    run_names = {2: "二連刻", 3: "大三連刻", 4: "大四連刻"}
    ext_names = {3: "小三連刻", 4: "小四連刻", 5: "小五連刻"}
    for suit, nums in trip_nums_by_suit.items():
        nums_sorted = sorted(set(nums))
        run_start = None
        prev = None
        for n in [*nums_sorted, None]:
            if prev is not None and n == prev + 1:
                pass
            else:
                if run_start is not None:
                    run_end = prev
                    length = run_end - run_start + 1
                    if length in run_scores:
                        lines.append(
                            ScoreLine(run_names[length], run_scores[length], f"{suit} {run_start}-{run_end} triplets"),
                        )
                    if suit_of(pair) == suit and number_of(pair) in (run_start - 1, run_end + 1):
                        ext_len = length + 1
                        if ext_len in ext_scores:
                            lines.append(
                                ScoreLine(
                                    ext_names[ext_len],
                                    ext_scores[ext_len],
                                    f"{suit} {run_start}-{run_end} triplets + adjoining pair",
                                ),
                            )
                run_start = n
            prev = n

    # 31: 삼색삼절고 (three consecutive numbers, one triplet per suit, all three suits)
    for n in range(1, 8):
        for perm in itertools.permutations(SUITS):
            if all(("triplet", f"{n + i}{perm[i]}") in groups for i in range(3)):
                lines.append(ScoreLine("三色三節高", 10, f"{n}-{n + 2} triplets split across all three suits"))
                break

    # 32: 노소커
    for suit in SUITS:
        if ("triplet", f"1{suit}") in groups and ("triplet", f"9{suit}") in groups:
            lines.append(ScoreLine("老少刻", 3, f"{suit} 1s and 9s both tripled"))

    # 36/37: 일기통관/삼색통관
    for suit in SUITS:
        if all(("sequence", suit, s) in groups for s in (1, 4, 7)):
            pts = 20 if flags.concealed else 10
            lines.append(ScoreLine("一條龍", pts, f"{suit} runs 1-9 in one suit"))
    for perm in itertools.permutations(SUITS):
        if all(("sequence", perm[i], 1 + 3 * i) in groups for i in range(3)):
            pts = 15 if flags.concealed else 8
            lines.append(ScoreLine("三條龍", pts, "runs 1-9 split across all three suits"))
            break

    # 53: 찬타/준찬타 (every group + the pair touches a terminal or honor)
    def _touches_terminal_or_honor(group) -> bool:
        if group[0] == "triplet":
            return is_terminal(group[1]) or is_honor(group[1])
        return group[2] in (1, 7)  # sequence starting at 1 or 7 includes a 1 or a 9

    if all(_touches_terminal_or_honor(g) for g in groups) and (is_terminal(pair) or is_honor(pair)):
        if any(is_honor(g[1]) for g in triplets) or is_honor(pair):
            lines.append(ScoreLine("全帶", 15, "every group touches a terminal or honour"))
        else:
            lines.append(ScoreLine("純全帶", 30, "every group touches a terminal, no honours"))

    return lines


def compute_score(
    text: str,
    seat_wind: str = "east",
    round_wind: str = "east",
    concealed: bool = True,
    tsumo: bool = False,
) -> ScoreResult:
    flags = ScoreFlags(seat_wind=seat_wind, round_wind=round_wind, concealed=concealed, tsumo=tsumo)

    tiles = parse_hand(text)
    hand_tiles, flower_tiles = split_flowers(tiles)

    if len(hand_tiles) != 14:
        raise ScoringError(
            f"Found {len(hand_tiles)} hand tiles (excluding flowers), but a complete hand needs exactly 14.",
        )

    winning_tile = hand_tiles[-1]
    no_flowers = not flower_tiles

    generic_lines, no_honors = _score_generic(hand_tiles, flags)
    flower_lines = _score_flowers(flower_tiles, flags)
    concealed_tsumo_lines = _score_concealed_tsumo(flags)

    shape_candidates: list[tuple[str, list[ScoreLine]]] = []

    if is_seven_pairs(hand_tiles):
        extra = _score_no_honor_family(no_honors, no_flowers, is_pinfu_shape=False)
        shape_candidates.append(("seven_pairs", extra))

    if is_thirteen_orphans(hand_tiles):
        extra = _score_no_honor_family(no_honors, no_flowers, is_pinfu_shape=False)
        shape_candidates.append(("thirteen_orphans", extra))

    for decomp in decompose_hand(hand_tiles):
        extra = _score_standard(decomp, flags, winning_tile, no_honors, no_flowers)
        shape_candidates.append(("standard", extra))

    if not shape_candidates:
        raise ScoringError(
            "Not a valid complete hand: doesn't break down into four sets + a pair, "
            "isn't seven pairs and isn't thirteen orphans.",
        )

    best_shape, best_extra, best_total = None, None, None
    for shape, extra in shape_candidates:
        lines = generic_lines + flower_lines + concealed_tsumo_lines + extra
        lines = lines + _chicken_duck(lines, flags)
        total = sum(line.points for line in lines)
        if best_total is None or total > best_total:
            best_shape, best_extra, best_total = shape, extra, total

    lines = generic_lines + flower_lines + concealed_tsumo_lines + best_extra
    lines = lines + _chicken_duck(lines, flags)
    total = sum(line.points for line in lines)

    return ScoreResult(
        shape=best_shape,
        hand_tiles=hand_tiles,
        flower_tiles=flower_tiles,
        winning_tile=winning_tile,
        lines=lines,
        total=total,
    )


__all__ = ["MahjongParseError", "ScoreFlags", "ScoreLine", "ScoreResult", "ScoringError", "compute_score"]
