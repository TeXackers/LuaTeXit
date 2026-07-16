"""
Custom PagerView layouts for the Tex module.
"""

from contextlib import suppress
from io import BytesIO
from typing import override

import discord
from cmdClient.Interaction import PagerView
from discord import Interaction
from discord.ui import Button


class TexPagerView(PagerView):
    """
    PagerView with an extra button that lets the viewer download the
    underlying preamble as a `.sty` file named after the owning user's id.
    """

    def __init__(
        self,
        pages,
        preamble: str,
        userid: int,
        download_emoji: str = "📥",
        **kwargs,
    ) -> None:
        self._preamble = preamble
        self._userid = userid

        self._download_button: Button = Button(emoji=download_emoji, style=discord.ButtonStyle.grey)
        self._download_button.callback = self._on_download

        super().__init__(pages, **kwargs)

    @override
    def _render(self) -> None:
        super()._render()
        self._controls.add_item(self._download_button)

    @override
    def _disable_controls(self) -> None:
        super()._disable_controls()
        self._download_button.disabled = True

    async def _on_download(self, interaction: Interaction) -> None:
        file = discord.File(BytesIO(self._preamble.encode()), filename=f"{self._userid}.sty")
        self._download_button.disabled = True
        await interaction.response.send_message(file=file, ephemeral=True)
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)
