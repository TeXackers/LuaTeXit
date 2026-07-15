"""
Shared boilerplate for the ruleset-specific mahjong practice views: deal 14,
discard one and draw a replacement (with a live score preview) as many times
as you like, or end the simulation to see how your hand would have scored.

Ruleset-specific scoring lives in `hk_drawer_cmd.py`/`riichi_drawer_cmd.py`;
each supplies `BaseDrawerView._evaluate`, everything else here is generic.
"""

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import discord
from cmdClient.Layouts import Body, Footer
from discord import SelectOption
from discord.ui import ActionRow, Button, Container, LayoutView, Select

from .display import tile_str as _tile_str
from .tiles import HAND_TILE_NAMES
from .tiles import tile_sort_key as _tile_sort_key
from .wall import Wall

if TYPE_CHECKING:
    from discord import Emoji

HAND_SIZE = 14


@dataclass
class EvalResult:
    """The scoring outcome of one complete (14-tile) hand, ruleset-agnostic."""

    sort_value: int  # for ranking waits/best-of-session -- scale is ruleset-specific
    short_label: str  # e.g. "7番", "3飜", "役満" -- shown inline next to a wait tile
    detail_text: str  # full yaku breakdown, shown once the hand is actually won


class BaseDrawerView(LayoutView):
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
        self.best_label: str = "—"
        self._last_status: tuple[str, str] = ("none", "Not 聽牌 yet")

        self._select: Select = Select(placeholder="Choose a tile to discard...")
        self._select.callback = self._on_discard
        self._end_button: Button = Button(label="End simulation", style=discord.ButtonStyle.red)
        self._end_button.callback = self._on_end

        self._record("Dealt")
        self._render()

    def _evaluate(self, tiles: list[str]) -> EvalResult | None:
        """Score a complete 14-tile hand, or return None if it doesn't win."""
        raise NotImplementedError

    def _hand_text(self) -> str:
        return "".join(_tile_str(self.emojis_by_name, t) for t in self.hand)

    def _best_tenpai(self) -> tuple[str, list[tuple[str, EvalResult]]] | None:
        """
        Check every possible discard from the current 14-tile hand; return
        (discard_tile, [(wait_tile, EvalResult), ...]) for whichever discard leaves
        the most winning tiles to wait on, or None if no discard reaches tenpai (聽牌).
        """
        best: tuple[str, list[tuple[str, EvalResult]]] | None = None
        for i, discard in enumerate(self.hand):
            candidate13 = self.hand[:i] + self.hand[i + 1 :]
            waits: list[tuple[str, EvalResult]] = []
            for wait_tile in HAND_TILE_NAMES:
                result = self._evaluate([*candidate13, wait_tile])
                if result is not None:
                    waits.append((wait_tile, result))
            if waits and (best is None or len(waits) > len(best[1])):
                best = (discard, waits)
        return best

    def _compute_status(self) -> tuple[str, int, str, str]:
        """Return (kind, sort_value, label, text): kind is one of 'win'/'tenpai'/'none'."""
        won = self._evaluate(self.hand)
        if won is not None:
            return ("win", won.sort_value, won.short_label, f"**You already have a winning hand!** {won.detail_text}")

        tenpai = self._best_tenpai()
        if tenpai is None:
            return ("none", 0, "", "Not 聽牌 yet")

        discard, waits = tenpai
        best = max(waits, key=lambda w: w[1].sort_value)[1]
        waits_text = ", ".join(
            f"{_tile_str(self.emojis_by_name, t)} ({r.short_label})"
            for t, r in sorted(waits, key=lambda w: -w[1].sort_value)
        )
        text = f"Discard {_tile_str(self.emojis_by_name, discard)} to reach 聽牌 [tenpai/ting paai], waiting on: {waits_text}"
        return ("tenpai", best.sort_value, best.short_label, text)

    def _status_short(self, kind: str, label: str) -> str:
        if kind == "win":
            return f": won! ({label})"
        if kind == "tenpai":
            return f": 聽牌 ({label})"
        return ""

    def _record(self, action: str) -> None:
        """Recompute the current status, log a one-line history entry, and track the session best."""
        kind, sort_value, label, text = self._compute_status()
        self._last_status = (kind, text)
        if sort_value > self.best_score:
            self.best_score = sort_value
            self.best_label = label
        self.history.append(f"{len(self.history)}. ({action}){self._status_short(kind, label)}")

    def _render(self) -> None:
        self.clear_items()

        kind, status_text = self._last_status
        if self.ended:
            if kind == "win":
                status_text = f"## You won!\n{status_text}"
            else:
                status_text = (
                    "## Simulation ended without completing a hand.\n"
                    f"**Best potential this session:** {self.best_label}"
                )

        recent_history = "\n".join(f"{line}" for line in self.history[-6:])

        body = (
            f"**Hand**\n# {self._hand_text()}\n"
            f"Discards: {len(self.discards)} | Remaining: {self.wall.remaining} | "
            f"Best so far: {self.best_label}\n\n"
            f"**Recent turns**\n{recent_history}\n\n"
            f"{status_text}"
        )
        container = Container(
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

    @override
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

    @override
    async def on_timeout(self) -> None:
        self.ended = True
        self._render()
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)
