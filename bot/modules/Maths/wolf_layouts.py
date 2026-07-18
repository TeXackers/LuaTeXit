"""
Layout construction specific to the Maths module.
"""

from typing import TYPE_CHECKING, override

import discord
from cmdClient.Interaction import PagerView
from discord.ui import ActionRow, Button

if TYPE_CHECKING:
    from cmdClient.Interaction import PagerEmoji

MORE_EMOJI = "👇"


class TeaserPagerView(PagerView):
    """
    Custom PagerView for Wolfram command that initially reveals only its start page with a single "More" button (plus delete) and expands in place into the full PagerView controls once that button is pressed.

    Stays largely true to the original Para's output
    """

    def __init__(self, pages, *, more_emoji: PagerEmoji = MORE_EMOJI, **kwargs) -> None:
        self.expanded: bool = False
        self._more_button: Button = Button(emoji=more_emoji, style=discord.ButtonStyle.grey)
        self._more_button.callback = self._on_more

        super().__init__(pages, **kwargs)

    @override
    def _render(self) -> None:
        if not self.expanded and len(self.pages) > 1:
            self.clear_items()

            controls = ActionRow()
            controls.add_item(self._more_button)
            controls.add_item(self._delete_button)

            self.add_item(self.pages[self.page])
            self.add_item(controls)
            return

        super()._render()

    @override
    def _disable_controls(self) -> None:
        super()._disable_controls()
        self._more_button.disabled = True

    async def _on_more(self, interaction: discord.Interaction) -> None:
        self.expanded = True
        self._render()
        await interaction.response.edit_message(view=self)
