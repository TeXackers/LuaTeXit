"""
Interactive pagination using Components V2 (LayoutView), replacing reaction-based paging.
"""

from contextlib import suppress
from typing import TYPE_CHECKING, override

import discord
from discord import Interaction, Member, User
from discord.ui import ActionRow, Button, LayoutView

from .Context import Context

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord import Emoji, PartialEmoji
    from discord.ui import Container

    PagerEmoji = str | Emoji | PartialEmoji


LEFT_EMOJI = "⏪"
RIGHT_EMOJI = "⏩"
CANCEL_EMOJI = "❌"


class PagerView(LayoutView):
    """
    A LayoutView that pages through a sequence of pre-built Containers,
    using buttons for navigation instead of reactions.

    Parameters
    ----------
    pages: Sequence[Container]
        The pages to display, one Container per page.
    author: User | Member | None
        If given, only this user may use the navigation buttons.
        If None, the pager is unlocked and anyone may use it.
    start_page: int
        The index of the page to display first.
    timeout: float | None
        Seconds of inactivity before the pager stops accepting input
        and disables its buttons. Requires `self.message` to be set
        after sending for the buttons to actually be disabled on timeout.
    left_emoji: str | Emoji | PartialEmoji
        Emoji for the "previous page" button. Defaults to a unicode emoji.
        Pass a `discord.Emoji`/`discord.PartialEmoji` to use a custom (e.g. application) emoji instead -
        resolve it beforehand with `await client.fetch_application_emojis()`, since PagerView has
        no client/context of its own to fetch one with.
    right_emoji: str | Emoji | PartialEmoji
        Emoji for the "next page" button. See `left_emoji`.
    delete_emoji: str | Emoji | PartialEmoji
        Emoji for the delete button. See `left_emoji`.
    """

    def __init__(
        self,
        pages: Sequence[Container],
        locked: bool = True,
        author: User | Member | None = None,
        start_page: int = 0,
        timeout: float | None = 300,
        left_emoji: PagerEmoji = LEFT_EMOJI,
        right_emoji: PagerEmoji = RIGHT_EMOJI,
        delete_emoji: PagerEmoji = CANCEL_EMOJI,
    ) -> None:
        if not pages:
            raise ValueError("PagerView cannot page with no pages.")
        if not (0 <= start_page < len(pages)):
            raise ValueError("start_page is out of range for the provided pages.")

        super().__init__(timeout=timeout)

        self.pages: Sequence[Container] = pages
        self.locked: bool = locked
        self.author: User | Member | None = author
        self.page: int = start_page
        self.message: discord.Message | None = None

        self._prev_button: Button = Button(emoji=left_emoji, style=discord.ButtonStyle.grey)
        self._prev_button.callback = self._on_prev

        self._indicator_button: Button = Button(style=discord.ButtonStyle.grey, disabled=True)

        self._next_button: Button = Button(
            emoji=right_emoji,
            style=discord.ButtonStyle.grey,
        )
        self._next_button.callback = self._on_next

        self._delete_button: Button = Button(emoji=delete_emoji, style=discord.ButtonStyle.grey)
        self._delete_button.callback = self._on_delete

        self._controls: ActionRow = ActionRow()

        self._render()

    def _render(self) -> None:
        """Rebuild the view's items to show the current page and up-to-date controls."""
        self.clear_items()

        self._indicator_button.label = f"{self.page + 1}/{len(self.pages)}"

        self._controls.clear_items()
        if len(self.pages) > 1:
            self._controls.add_item(self._prev_button)
            self._controls.add_item(self._indicator_button)
            self._controls.add_item(self._next_button)
        self._controls.add_item(self._delete_button)

        self.add_item(self.pages[self.page])
        self.add_item(self._controls)

    def _disable_controls(self) -> None:
        self._prev_button.disabled = True
        self._next_button.disabled = True
        self._delete_button.disabled = True

    @override
    async def interaction_check(self, interaction: Interaction) -> bool:
        match self.locked, interaction.user != self.author:
            case True, True:
                from wards import is_dev  # noqa

                ctx: Context = Context(interaction.client, author=interaction.user)
                if await is_dev.run(ctx):
                    return True
                await interaction.response.send_message("You can't control this pager.", ephemeral=True)
                return False
            case _, _:
                return True
        return True

    async def _on_begin(self, interaction: Interaction) -> None:
        self.page = 0
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_prev(self, interaction: Interaction) -> None:
        self.page = (self.page - 1) % len(self.pages)
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_next(self, interaction: Interaction) -> None:
        self.page = (self.page + 1) % len(self.pages)
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_end(self, interaction: Interaction) -> None:
        self.page = len(self.pages) - 1
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_delete(self, interaction: Interaction) -> None:
        if self.author is not None and interaction.user != self.author:
            await interaction.response.send_message(
                "You must have invoked the command to be able to delete this pager.",
                ephemeral=True,
            )
            return
        self.stop()
        await interaction.response.defer()
        with suppress(discord.HTTPException):
            await interaction.delete_original_response()

    @override
    async def on_timeout(self) -> None:
        self._disable_controls()
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)
