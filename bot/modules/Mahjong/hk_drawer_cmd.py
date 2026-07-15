from typing import override

from cmdClient import Context  # noqa

from .display import render_note
from .drawer_base import BaseDrawerView, EvalResult
from .module import mahjong_module as module
from .scoring import ScoringError, compute_score


class HongKongDrawerView(BaseDrawerView):
    @override
    def _evaluate(self, tiles: list[str]) -> EvalResult | None:
        text = ",".join(tiles)
        try:
            result = compute_score(text, zimo=True)
        except ScoringError:
            return None

        breakdown = "\n".join(
            f"- {line.name}: {render_note(self.emojis_by_name, line.note)} ({line.points}番)" for line in result.lines
        )
        return EvalResult(
            sort_value=result.total,
            short_label=f"{result.total}番",
            detail_text=f"{result.total}番 = {result.points} pts\n{breakdown or 'No 役 matched.'}",
        )


@module.cmd(
    "mahjongdraw",
    desc="Practise building a Hong Kong-rule mahjong hand: draw, discard, and see your score live.",
    aliases=["mj", "hkdraw"],
)
async def cmd_mahjongdraw(ctx: Context):
    """
    Usage``:
        {prefix}mahjongdraw
    Description:
        Deals you 14 tiles from a shuffled solo wall, scored under Hong Kong
        rules (see `;help score`). Pick a tile to discard from the dropdown
        and you'll draw a replacement, with a live score preview each time.
        Hit "End simulation" whenever you want to see your final hand and
        score (or continue discarding). See `;help riichidraw` for the
        Riichi (Japanese) version.
    """
    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    view = HongKongDrawerView(ctx.author, emojis_by_name)
    message = await ctx.reply(view=view)
    view.message = message
