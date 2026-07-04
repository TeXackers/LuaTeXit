from __future__ import annotations

import discord
from cmdClient import Context  # noqa
from cmdClient.Layouts import TextEmbed

from .display import render_note, tile_str
from .module import mahjong_module as module
from .scoring import MahjongParseError, ScoringError, compute_score
from .tiles import WINDS


@module.cmd(
    "score",
    desc="Score a Hong Kong mahjong hand.",
    aliases=["mscore", "hkscore"],
    flags=["seat=", "round=", "drawn", "open"],
)
async def cmd_score(ctx: Context, flags: dict):
    """Usage``:
        {prefix}score <hand> [-seat=<wind>] [-round=<wind>] [-drawn] [-open]
    Description:
        Scores a complete 14-tile Hong Kong mahjong hand against the structural
        subset of the house rules (no riichi/kan/wall-state rules; those need
        live game context this command doesn't have).
        Tiles are written in compact notation, delimited by `,`, `;`, or newlines:
            `m`/`p`/`s` suffix: a run of digits for that suit, e.g. `123m` = 1maan 2maan 3maan.
            `z` suffix: winds then dragons, 1-7 = east,south,west,north,white,faat,middle.
            `f` suffix: flowers, 1-8 = zuk,mai,laan,guk,spring,summer,autumn,winter.
        Bare tile names (`east`, `5tong`, ...) also work directly.
        The last tile listed is treated as your winning tile.
        Flower tiles don't count toward the 14 so list them in addition.
    Flags::
        seat=<wind>: Your seat wind (east/south/west/north). Default east.
        round=<wind>: The round wind. Default east.
        drawn: Score as a self-draw win, instead of 榮(和).
        open: Score as a fully open (called) hand, instead of concealed.
    Examples``:
        {prefix}score 123m456p789s11z555z
        {prefix}score 111222333444m11z -drawn
        {prefix}score 123m123m123m123m11z -seat=south -open
    """
    if not ctx.args:
        return await ctx.error_reply("Please provide a hand to score.")

    seat_wind = (flags["seat"] or "east").lower()
    round_wind = (flags["round"] or "east").lower()
    if seat_wind not in WINDS or round_wind not in WINDS:
        return await ctx.error_reply(f"`seat`/`round` must be one of: {', '.join(WINDS)}.")

    try:
        result = compute_score(
            ctx.args,
            seat_wind=seat_wind,
            round_wind=round_wind,
            concealed=not flags["open"],
            tsumo=bool(flags["drawn"]),
        )
    except (MahjongParseError, ScoringError) as e:
        return await ctx.error_reply(str(e))

    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    hand_display = "".join(tile_str(emojis_by_name, t) for t in result.hand_tiles)
    flowers_display = "".join(tile_str(emojis_by_name, t) for t in result.flower_tiles) if result.flower_tiles else ""

    lines = [f"- {line.name}: {render_note(emojis_by_name, line.note)} ({line.points} pt)" for line in result.lines]
    score_lines = "\n".join(lines) if lines else "No 役 matched."
    body = f"**Total: {result.total} pts**\n{score_lines}"
    footer = (
        f"Shape: {result.shape.replace('_', ' ')} | Winning tile: {result.winning_tile} | "
        f"Seat: {seat_wind} | Round: {round_wind} | "
        f"{'Concealed' if not flags['open'] else 'Open'}, {'自摸' if flags['drawn'] else '榮和'}"
    )

    return await ctx.reply(
        view=TextEmbed(
            header=f"{hand_display}{flowers_display}",
            body=body,
            footer=footer,
            accent_colour=discord.Colour.from_str("#2D6A1B"),
        ),
    )
