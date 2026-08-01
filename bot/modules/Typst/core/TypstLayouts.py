"""
Output view for the `typst` command, using Components V2 (LayoutView).
"""

from contextlib import suppress
from typing import override

import discord
from cmdClient.Layouts import Body
from discord import Interaction, MediaGalleryItem, Member, User
from discord.ui import ActionRow, Button, LayoutView, MediaGallery, Separator, TextDisplay


class TypstOutputView(LayoutView):
    """
    Displays a compiled Typst image, with buttons to toggle the source/error
    text and to delete the output.

    Parameters
    ----------
    source: str
        The Typst source that was compiled.
    error: str | None
        The compile error, if compilation failed.
    image_filenames: list[str]
        Filenames of the attached output images (one per page), each referenced via
        `attachment://{filename}`.
    author: User | Member
        The user who ran the command; only they (or someone with
        `manage_messages`) may use the buttons.
    header_name: str
        The (possibly empty) name/mention line shown above the output per the author's `namestyle` setting.
    """

    def __init__(
        self,
        source: str,
        error: str | None,
        image_filenames: list[str],
        author: User | Member,
        header_name: str = "",
        timeout: float | None = 300,
    ) -> None:
        super().__init__(timeout=timeout)

        self.source = source
        self.error = error
        self.image_filenames = image_filenames
        self.author = author
        self.header_name = header_name
        self.shown = False
        self.message: discord.Message | None = None

        self._toggle_button: Button = Button(style=discord.ButtonStyle.grey)
        self._toggle_button.callback = self._on_toggle

        self._delete_button: Button = Button(emoji="❌", style=discord.ButtonStyle.grey)
        self._delete_button.callback = self._on_delete

        self._render()

    def _render(self) -> None:
        """Rebuild the view's items to show the current state."""
        self.clear_items()

        if self.header_name:
            self.add_item(TextDisplay(self.header_name))
        if self.shown:
            text = self.error or self.source
            syntax = "" if self.error else "typst"
            self.add_item(Body(f"```{syntax}\n{text}\n```"))
        for i, filename in enumerate(self.image_filenames):
            if i > 0:
                self.add_item(Separator(visible=False))
            self.add_item(MediaGallery(MediaGalleryItem(f"attachment://{filename}")))

        label_subject = "error" if self.error else "source"
        self._toggle_button.label = f"{'Hide' if self.shown else 'Show'} {label_subject}"

        self.add_item(ActionRow(self._toggle_button, self._delete_button))

    def _disable_controls(self) -> None:
        self._toggle_button.disabled = True
        self._delete_button.disabled = True

    @override
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        if (
            interaction.guild
            and isinstance(interaction.user, Member)
            and interaction.channel is not None
            and interaction.channel.permissions_for(interaction.user).manage_messages
        ):
            return True
        await interaction.response.send_message("You can't control this output.", ephemeral=True)
        return False

    async def _on_toggle(self, interaction: Interaction) -> None:
        self.shown = not self.shown
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_delete(self, interaction: Interaction) -> None:
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
