from cmdClient import Context  # noqa

from .display import render_note
from .drawer_base import BaseDrawerView, EvalResult
from .module import mahjong_module as module
from .scoring import RiichiRuleset, ScoringError, describe_yakuman

_riichi = RiichiRuleset()


class RiichiDrawerView(BaseDrawerView):
    def _evaluate(self, tiles: list[str]) -> EvalResult | None:
        text = ",".join(tiles)
        try:
            result = _riichi.compute(text, tsumo=True)
        except ScoringError:
            return None

        if result.is_yakuman:
            breakdown = "\n".join(
                f"- {line.name}: {render_note(self.emojis_by_name, line.note)} ({describe_yakuman(line.points)})"
                for line in result.lines
            )
            summary = result.limit_name
            short_label = result.limit_name
        else:
            breakdown = "\n".join(
                f"- {line.name}: {render_note(self.emojis_by_name, line.note)} ({line.points}飜)" for line in result.lines
            )
            summary = f"{result.han}飜 ({result.limit_name})" if result.limit_name else f"{result.han}飜 {result.fu}符"
            short_label = f"{result.han}飜"

        return EvalResult(
            sort_value=result.total_points,
            short_label=short_label,
            detail_text=f"{summary}\n{breakdown or 'No yaku matched.'}",
        )


@module.cmd(
    "riichidraw",
    desc="Practise building a Riichi (Japanese) mahjong hand: draw, discard, and see your score live.",
    aliases=["jdraw"],
)
async def cmd_riichidraw(ctx: Context):
    """
    Usage``:
        {prefix}riichidraw
    Description:
        Deals you 14 tiles from a shuffled solo wall, scored under Riichi
        (Japanese) rules (see `;help riichi`) as a dealer self-draw (東家自摸)
        with no riichi/dora, since those depend on things a solo practice
        hand can't know. Pick a tile to discard from the dropdown and you'll
        draw a replacement, with a live score preview each time. Hit "End
        simulation" whenever you want to see your final hand and score (or
        continue discarding). See `;help mahjongdraw` for the Hong Kong
        version.
    """
    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    view = RiichiDrawerView(ctx.author, emojis_by_name)
    message = await ctx.reply(view=view)
    view.message = message
