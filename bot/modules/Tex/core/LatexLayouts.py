"""
Custom PagerView layouts for the Tex module.
"""

import asyncio
from contextlib import suppress
from io import BytesIO
from typing import override

import discord
from cmdClient.Interaction import PagerView
from discord import Interaction
from discord.ui import Button

DOWNLOAD_TIMEOUT = 300


class TexPagerView(PagerView):
    """
    PagerView with an extra button that lets the viewer download the
    underlying preamble as a `.sty` file named after the owning user's id.

    The download button expires on its own after `DOWNLOAD_TIMEOUT` seconds,
    independently of the pager's inactivity timeout (which resets on every
    navigation click and would otherwise keep the button alive indefinitely).
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

        self._download_expiry_task: asyncio.Task = asyncio.ensure_future(self._expire_download_button())

    @override
    def _render(self) -> None:
        super()._render()
        self._controls.add_item(self._download_button)

    @override
    def _disable_controls(self) -> None:
        super()._disable_controls()
        self._download_button.disabled = True

    async def _expire_download_button(self) -> None:
        await asyncio.sleep(DOWNLOAD_TIMEOUT)
        if self._download_button.disabled:
            return
        self._download_button.disabled = True
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)

    @override
    def stop(self) -> None:
        self._download_expiry_task.cancel()
        super().stop()

    @override
    async def on_timeout(self) -> None:
        self._download_expiry_task.cancel()
        await super().on_timeout()

    async def _on_download(self, interaction: Interaction) -> None:
        self._download_expiry_task.cancel()
        file = discord.File(BytesIO(self._preamble.encode()), filename=f"{self._userid}.sty")
        self._download_button.disabled = True
        await interaction.response.send_message(file=file, ephemeral=True)
        if self.message is not None:
            with suppress(discord.HTTPException):
                await self.message.edit(view=self)
