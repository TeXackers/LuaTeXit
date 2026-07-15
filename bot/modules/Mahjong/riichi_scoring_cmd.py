import discord
from cmdClient import Context  # noqa
from cmdClient.Layouts import TextEmbed

from .display import render_note, tile_str
from .module import mahjong_module as module
from .scoring import MahjongParseError, RiichiRuleset, RiichiScoreResult, ScoringError, describe_yakuman
from .tiles import WINDS, parse_hand, tile_sort_key

_riichi = RiichiRuleset()


def _parse_indicators(raw: str | None) -> list[str]:
    return parse_hand(raw) if raw else []


def _payments_text(result: RiichiScoreResult) -> str:
    if "ron" in result.payments:
        return f"Payout: {result.payments['ron']} points"
    if "tsumo_dealer" in result.payments:
        return f"Payout: {result.payments['tsumo_each']} (子), {result.payments['tsumo_dealer']} (親)"
    return f"Payout: {result.payments['tsumo_each']} from each player"


@module.cmd(
    "riichi",
    desc="Score a Riichi (Japanese) mahjong hand.",
    aliases=["jscore", "riichiscore"],
    flags=[
        "seat=",
        "round=",
        "tsumo",
        "riichi",
        "double",
        "dora=",
        "uradora",
        "akadora=",
        # weird funky ones
        "ippatsu",
        "haitei",
        "houtei",
        "rinshan",
        "chankan",
        "renhou",
        "tenhou",
        "chiihou",
        "honba=",
    ],
)
async def cmd_riichi(ctx: Context, flags: dict):
    """Usage``:
        {prefix}riichi <hand> [-seat=<wind>] [-round=<wind>] [-tsumo] [flags...]
    Description:
        Scores a complete Riichi mahjong hand per JPML rules. Tiles use the same
        compact notation as `;score` (`m`/`p`/`s`/`z` suffixes). Also
        accepts melds; `[..]` for open chi/pon/minkan,
        and `(..)` for a closed kan. The last tile listed is your winning tile.
    Flags::
        seat=: Your seat wind. Default east (dealer).
        round=: The round wind. Default east.
        tsumo: Self-draw (tsumo) win, instead of ron.
        riichi: Riichi declared (needs a concealed hand).
        double: Double riichi.
        ippatsu: Won within one go-around of riichi.
        dora=: Dora indicator tiles.
        uradora: Also count your dora indicators as uradora.
        akadora=: Red-5 tile count. Default 0.
        honba=: Honba (repeat) stick count. Default 0.
    Examples``:
        {prefix}riichi 2256m456789p789s7m
        {prefix}riichi 123567p3345s[111z]3s --dora 9p --tsumo --akadora 1

    Special Flags::
        haitei: Won on the last tile of the wall.
        houtei: Won on the last discard.
        rinshan: Won on a kan draw.
        chankan: Won by robbing a kan.
        renhou: Won on the first turn (dealer only).
        tenhou: Dealer won on the first turn.
        chiihou: Non-dealer won on the first turn.
    """
    if not ctx.args:
        return await ctx.reply("Please provide a hand to score.")

    seat_wind = (flags["seat"] or "east").lower()
    round_wind = (flags["round"] or "east").lower()
    if seat_wind not in WINDS or round_wind not in WINDS:
        return await ctx.reply(f"`seat`/`round` must be one of: {', '.join(WINDS)}.")

    try:
        honba = int(flags["honba"] or 0)
        akadora = int(flags["akadora"] or 0)
    except ValueError:
        return await ctx.reply("`honba` must be a whole number.")

    try:
        result = _riichi.compute(
            ctx.args,
            seat_wind=seat_wind,
            round_wind=round_wind,
            tsumo=bool(flags["tsumo"]),
            riichi=bool(flags["riichi"]),
            double_riichi=bool(flags["double"]),
            ippatsu=bool(flags["ippatsu"]),
            haitei=bool(flags["haitei"]),
            houtei=bool(flags["houtei"]),
            rinshan=bool(flags["rinshan"]),
            chankan=bool(flags["chankan"]),
            renhou=bool(flags["renhou"]),
            tenhou=bool(flags["tenhou"]),
            chiihou=bool(flags["chiihou"]),
            honba=honba,
            dora_indicators=_parse_indicators(flags["dora"]),
            uradora=bool(flags["uradora"]),
            akadora=akadora,
        )
    except (MahjongParseError, ScoringError) as e:
        return await ctx.error_reply(str(e))

    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    hand_display = "".join(tile_str(emojis_by_name, t) for t in sorted(result.hand_tiles, key=tile_sort_key))

    if result.is_yakuman:
        breakdown = [
            f"- {line.name}: {render_note(emojis_by_name, line.note)} ({describe_yakuman(line.points)})"
            for line in result.lines
        ]
    else:
        breakdown = [
            f"- {line.name}: {render_note(emojis_by_name, line.note)} ({line.points}飜)" for line in result.lines
        ]
    yaku_text = "\n".join(breakdown) if breakdown else "No yaku matched."
    if result.is_yakuman:
        summary = f"### {result.limit_name}"
    elif result.limit_name:
        summary = f"### {result.han}飜 ({result.limit_name})"
    else:
        summary = f"### {result.han}飜 {result.fu}符"
    body = f"{summary}\n{_payments_text(result)}\n\n**Breakdown**\n{yaku_text}"
    footer = (
        f"Winning tile: {emojis_by_name[result.winning_tile]} | Seat: {emojis_by_name[seat_wind]} | Round: {emojis_by_name[round_wind]} | "
        f"{'自摸 (Tsumo)' if flags['tsumo'] else '榮和 (Ron)'}"
    )

    return await ctx.reply(
        view=TextEmbed(
            header=hand_display,
            body=body,
            footer=footer,
            accent_colour=discord.Colour.from_str("#2D6A1B"),
        ),
    )
