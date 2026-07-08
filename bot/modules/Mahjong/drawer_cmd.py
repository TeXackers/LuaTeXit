"""
A single-player interactive hand-building practice tool: deal 14, discard one
and draw a replacement (with a live score preview) as many times as you like,
or end the simulation to see how your hand would have scored.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from cmdClient import Context  # noqa
from cmdClient.Layouts import Body, Footer, Header
from discord import SelectOption
from discord.ui import ActionRow, Button, Container, LayoutView, Select, Separator
from wards import is_master

from .display import render_note
from .display import tile_str as _tile_str
from .module import mahjong_module as module
from .scoring import ScoringError, compute_score
from .tiles import HAND_TILE_NAMES
from .tiles import tile_sort_key as _tile_sort_key
from .wall import Wall

if TYPE_CHECKING:
    from discord import Emoji

HAND_SIZE = 14


def _score_lines_text(result, emojis_by_name: dict) -> str:
    if not result.lines:
        return "No yaku matched."
    return "\n".join(
        f"- {line.name}: {render_note(emojis_by_name, line.note)} ({line.points} pt)" for line in result.lines
    )


class MahjongDrawerView(LayoutView):
    def __init__(self, author: discord.User | discord.Member, emojis_by_name: dict[str, Emoji]):
        super().__init__(timeout=600)
        self.author = author
        self.emojis_by_name = emojis_by_name
        self.wall = Wall()
        self.hand: list[str] = sorted((self.wall.draw() for _ in range(HAND_SIZE)), key=_tile_sort_key)
        self.discards: list[str] = []
        self.message: discord.Message | None = None
        self.ended: bool = False

        self.history: list[str] = []
        self.best_score: int = 0
        self._last_status: tuple[str, int, str] = ("none", 0, "")

        self._select: Select = Select(placeholder="Choose a tile to discard...")
        self._select.callback = self._on_discard
        self._end_button: Button = Button(label="End simulation", style=discord.ButtonStyle.red)
        self._end_button.callback = self._on_end

        self._record("Dealt")
        self._render()

    def _hand_text(self) -> str:
        return "".join(_tile_str(self.emojis_by_name, t) for t in self.hand)

    def _best_tenpai(self) -> tuple[str, list[tuple[str, int]]] | None:
        """
        Check every possible discard from the current 14-tile hand; return
        (discard_tile, [(wait_tile, score), ...]) for whichever discard leaves
        the most winning tiles to wait on, or None if no discard reaches tenpai (聽牌).
        """
        best: tuple[str, list[tuple[str, int]]] | None = None
        for i, discard in enumerate(self.hand):
            candidate13 = self.hand[:i] + self.hand[i + 1 :]
            waits: list[tuple[str, int]] = []
            for wait_tile in HAND_TILE_NAMES:
                text = ",".join([*candidate13, wait_tile])
                try:
                    result = compute_score(text, concealed=True, tsumo=True)
                except ScoringError:
                    continue
                waits.append((wait_tile, result.total))
            if waits and (best is None or len(waits) > len(best[1])):
                best = (discard, waits)
        return best

    def _compute_status(self) -> tuple[str, int, str]:
        """Return (kind, score, text): kind is one of 'win'/'tenpai'/'none'."""
        text = ",".join(self.hand)
        try:
            result = compute_score(text, concealed=True, tsumo=True)
        except ScoringError:
            pass
        else:
            return (
                "win",
                result.total,
                f"**You already have a winning hand!** {result.total} points\n"
                f"{_score_lines_text(result, self.emojis_by_name)}",
            )

        tenpai = self._best_tenpai()
        if tenpai is None:
            return (
                "none",
                0,
                "Not 聽牌 yet",
            )

        discard, waits = tenpai
        best_wait_score = max(pts for _, pts in waits)
        waits_text = ", ".join(
            f"{_tile_str(self.emojis_by_name, t)} ({pts}pt)" for t, pts in sorted(waits, key=lambda w: -w[1])
        )
        text = f"Discard {_tile_str(self.emojis_by_name, discard)} to reach 聽牌 [tenpai/ting paai], waiting on: {waits_text}"
        return ("tenpai", best_wait_score, text)

    def _status_short(self, kind: str, score: int) -> str:
        if kind == "win":
            return f": won! ({score}pt)"
        if kind == "tenpai":
            return f": 聽牌 ({score}pt)"
        return ""

    def _record(self, action: str) -> None:
        """Recompute the current status, log a one-line history entry, and track the session best."""
        status = self._compute_status()
        self._last_status = status
        kind, score, _ = status
        if score > self.best_score:
            self.best_score = score
        self.history.append(f"{len(self.history)}. ({action}){self._status_short(kind, score)}")

    def _render(self) -> None:
        self.clear_items()

        kind, _, status_text = self._last_status
        if self.ended:
            if kind == "win":
                status_text = f"## You won!\n{status_text}"
            else:
                status_text = (
                    "## Simulation ended without completing a hand.\n"
                    f"**Best potential this session:** {self.best_score} points"
                )

        recent_history = "\n".join(f"{line}" for line in self.history[-6:])

        body = (
            f"**Hand**\n# {self._hand_text()}\n"
            f"Discards: {len(self.discards)} | Remaining: {self.wall.remaining} | "
            f"Best so far: {self.best_score} points\n\n"
            f"**Recent turns**\n{recent_history}\n\n"
            f"{status_text}"
        )
        container = Container(
            # Header("Mahjong practice"),
            # Separator(),
            Body(body),
            Footer(f"{self.author.display_name} | {discord.utils.format_dt(discord.utils.utcnow(), 'F')}"),
            accent_color=discord.Color.from_str("#2D6A1B"),
        )
        self.add_item(container)

        if not self.ended:
            self._select.options = [
                SelectOption(
                    label=tile,
                    value=str(i),
                    emoji=self.emojis_by_name.get(tile),
                )
                for i, tile in enumerate(self.hand)
            ]
            self.add_item(ActionRow(self._select))
            self.add_item(ActionRow(self._end_button))
        else:
            self._select.disabled = True
            self._end_button.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("This isn't your practice hand.", ephemeral=True)
            return False
        return True

    async def _on_discard(self, interaction: discord.Interaction) -> None:
        idx = int(self._select.values[0])
        tile = self.hand.pop(idx)
        self.discards.append(tile)

        if self.wall.remaining == 0:
            self.ended = True
        else:
            self.hand.append(self.wall.draw())
            self.hand.sort(key=_tile_sort_key)

        self._record(f"- {_tile_str(self.emojis_by_name, tile)}")
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_end(self, interaction: discord.Interaction) -> None:
        self.ended = True
        self._render()
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self) -> None:
        self.ended = True
        self._render()
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)


@module.cmd(
    "mahjongdraw",
    desc="Practise building a mahjong hand: draw, discard, and see your score live.",
    aliases=["mj"],
)
async def cmd_mahjongdraw(ctx: Context):
    """
    Usage``:
        {prefix}mahjongdraw
    Description:
        Deals you 14 tiles from a shuffled solo wall. Pick a tile to discard
        from the dropdown and you'll draw a replacement, with a live score
        preview each time. Hit the "End simulation" whenever you want to see
        your final hand and score (or continue discarding).
    """
    emojis = await ctx.client.fetch_application_emojis()
    emojis_by_name = {e.name: e for e in emojis}

    view = MahjongDrawerView(ctx.author, emojis_by_name)
    message = await ctx.reply(view=view)
    view.message = message
