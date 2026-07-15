import discord
from cmdClient import Context  # noqa
from cmdClient.Layouts import TextEmbed

from .display import render_note, tile_str
from .module import mahjong_module as module
from .scoring import MahjongParseError, ScoringError, compute_score
from .tiles import WINDS, tile_sort_key


@module.cmd(
    "score",
    desc="Score a mahjong hand using Hong Kong rules.",
    aliases=["hk"],
    flags=[
        "seat=",
        "round=",
        "zimo",
        "minfaan=",
        "cg",
        "hoidai",
        "hodai",
        "gshf",
        "gsg",
        "tinwu",
        "deiwu",
    ],
)
async def cmd_score(ctx: Context, flags: dict):
    """Usage``:
        {prefix}score <hand> [-seat=<wind>] [-round=<wind>] [-zimo] [flags...]
    Description:
        Scores a complete 14-tile Hong Kong mahjong hand per 홍콩족보.md (faan,
        capped at 13, converted to points via the half-spicy table). Tiles are
        written in compact notation (`m`/`p`/`s`/`z` suffixes). The last tile
        listed is treated as your winning tile. Whether the hand is open is read
        from the tiles themselves: `[123m]` for a called chi/pon/minkan, `(1111z)`
        for a closed kan -- a hand with no bracketed melds at all is fully
        concealed. See `;help riichi` for the full meld notation.
    Flags::
        seat=<wind>: Your seat wind (east/south/west/north). Default east.
        round=<wind>: The round wind. Default east.
        zimo: Score as a self-draw win, instead of 榮(和).
        minfaan=: Minimum faan required to win, on top of the flat 0-faan (雞糊) floor. Default 0.
        cg: 搶槓, robbed another player's added kong, instead of a normal win.
        hoidai: 海底撈月, drew the very last tile of the wall.
        hodai: 河底撈魚,  won off the final discard of the round.
        gshf: 槓上開花,  won on a kong replacement tile.
        gsg: 槓上槓,  won on a second consecutive kong replacement tile.
        tinwu: 天胡,  dealer's starting hand was already complete.
        deiwu: 地胡,  non-dealer won on the dealer's first discard.
    Examples``:
        {prefix}score 123m456p789s11z555z
        {prefix}score 111222333444m11z -zimo
        {prefix}score [123m][123m][123m][123m]11z -seat=south
    """
    if not ctx.args:
        return await ctx.error_reply("Please provide a hand to score.")

    seat_wind = (flags["seat"] or "east").lower()
    round_wind = (flags["round"] or "east").lower()
    if seat_wind not in WINDS or round_wind not in WINDS:
        return await ctx.error_reply(f"`seat`/`round` must be one of: {', '.join(WINDS)}.")

    try:
        min_faan = int(flags["minfaan"] or 0)
    except ValueError:
        return await ctx.error_reply("`minfaan` must be a whole number.")

    try:
        result = compute_score(
            ctx.args,
            seat_wind=seat_wind,
            round_wind=round_wind,
            zimo=bool(flags["zimo"]),
            min_faan=min_faan,
            cg=bool(flags["cg"]),
            hoidai=bool(flags["hoidai"]),
            hodai=bool(flags["hodai"]),
            gshf=bool(flags["gshf"]),
            gsg=bool(flags["gsg"]),
            tinwu=bool(flags["tinwu"]),
            deiwu=bool(flags["deiwu"]),
        )
    except (MahjongParseError, ScoringError) as e:
        return await ctx.error_reply(str(e))

    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    hand_display = "".join(tile_str(emojis_by_name, t) for t in sorted(result.hand_tiles, key=tile_sort_key))

    lines = [f"- {line.name}: {render_note(emojis_by_name, line.note)} ({line.points}番)" for line in result.lines]
    score_lines = "\n".join(lines) if lines else "No 役 matched."
    body = f"### {result.total}番 = {result.points} pts\n{score_lines}"
    footer = (
        f"Shape: {result.shape.replace('_', ' ')} | Winning tile: {tile_str(emojis_by_name, result.winning_tile)} | "
        f"Seat: {tile_str(emojis_by_name, seat_wind)} | Round: {tile_str(emojis_by_name, round_wind)}"
        # HK doesn't have "ron" so only show zimo
        f"{'| 自摸' if flags['zimo'] else ''}"
    )

    return await ctx.reply(
        view=TextEmbed(
            header=hand_display,
            body=body,
            footer=footer,
            accent_colour=discord.Colour.from_str("#2D6A1B"),
        ),
    )
