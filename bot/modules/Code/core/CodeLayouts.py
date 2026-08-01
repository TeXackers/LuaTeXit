"""
Output view for the `code` command, using Components V2 (LayoutView).
"""

from typing import override

import discord
from cmdClient.Interaction import PagerView
from cmdClient.Layouts import Body, Header
from discord import Interaction, MediaGalleryItem, Member, User
from discord.ui import Container, MediaGallery, Separator
from utils.lib import split_text

from modules.Github.GithubColours import GITHUB_LANG2COLOUR

_BLOCK_LENGTH = 1500
_MAX_HEIGHT = 30
_IMAGES_PER_PAGE = 3

# Our codeblock syntax tags to GitHub linguist's language names, for GITHUB_LANG2COLOUR lookup.
_LANG_DISPLAY_NAME = {"python": "Python", "r": "R"}
_DEFAULT_COLOUR = discord.Colour.from_str("#393A41")


def _lang_colour(syntax: str) -> discord.Colour:
    return GITHUB_LANG2COLOUR.get(_LANG_DISPLAY_NAME.get(syntax, syntax), _DEFAULT_COLOUR)


def _section_pages(title: str, text: str, syntax: str, colour: discord.Colour) -> list[Container]:
    """
    Split one section of text (source, or output/error) into codeblock-wrapped pages.
    """
    blocks = split_text(text, blocksize=_BLOCK_LENGTH, code=True, syntax=syntax, maxheight=_MAX_HEIGHT)
    pages = []
    for i, block in enumerate(blocks):
        heading = f"{title} ({i + 1}/{len(blocks)})" if len(blocks) > 1 else title
        pages.append(Container(Header(heading), Separator(), Body(block), accent_colour=colour))
    return pages


def _image_pages(image_filenames: list[str], colour: discord.Colour) -> list[Container]:
    """
    Groups plots `_IMAGES_PER_PAGE` to a page, so browsing several plots needs fewer clicks.
    """
    chunks = [image_filenames[i : i + _IMAGES_PER_PAGE] for i in range(0, len(image_filenames), _IMAGES_PER_PAGE)]
    pages = []
    n = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        heading = f"Plots ({i}/{n})" if n > 1 else ("Plot" if len(chunk) == 1 else "Plots")
        gallery = MediaGallery(*(MediaGalleryItem(f"attachment://{filename}") for filename in chunk))
        pages.append(Container(Header(heading), Separator(), gallery, accent_colour=colour))
    return pages


def build_code_pages(
    source: str,
    syntax: str,
    output: str,
    failed: bool,
    image_filenames: list[str],
    shown: bool,
) -> list[Container]:
    """
    Build the `Container` pages for a `code` run, for `ctx.pager_v2_pages`.
    Also (re)used by `CodeOutputView` itself when the "Show source" toggle flips.
    """
    colour = _lang_colour(syntax)
    pages: list[Container] = []
    if shown:
        pages += _section_pages("Source", source, syntax, colour)

    if output or failed:
        label = "Error" if failed else "Output"
        body = output or "-# [no output captured]"
        colour = discord.Colour.red() if failed else colour
        pages += _section_pages(label, body, "", colour)

    pages += _image_pages(image_filenames, colour)

    if not pages:
        pages.append(Container(Body("*(no output produced)*"), accent_colour=colour))

    return pages


class CodeOutputView(PagerView):
    """
    Pages through the result of running a Python/R snippet: any plot it produced,
    its captured stdout/stderr, and (toggleable) the source that produced it.

    Long source or output is split across multiple pages rather than truncated.
    Meant to be used as the `view_cls` for `ctx.pager_v2_pages`, which supplies
    the initial `pages`, `author`, and application-emoji `left_emoji`/`right_emoji`.

    Parameters
    ----------
    pages: list[Container]
        The initial pages, as built by `build_code_pages`.
    source: str
        The code that was run.
    syntax: str
        The codeblock language tag to highlight `source` with (e.g. "python", "r").
    output: str
        Captured stdout/stderr from the run. May be empty.
    failed: bool
        Whether the run failed (non-zero exit, or timed out).
    image_filenames: list[str]
        Filenames of any attached plot images, each referenced via `attachment://{filename}`
        on its own page. Empty if no plot was produced.
    shown: bool
        Whether the source section is included in `pages` already.
    """

    def __init__(
        self,
        pages: list[Container],
        source: str,
        syntax: str,
        output: str,
        failed: bool,
        image_filenames: list[str],
        shown: bool = False,
        **kwargs,
    ) -> None:
        self.source = source
        self.syntax = syntax
        self.output = output
        self.failed = failed
        self.image_filenames = image_filenames
        self.shown = shown

        self._toggle_button: discord.ui.Button = discord.ui.Button(style=discord.ButtonStyle.grey)
        self._toggle_button.callback = self._on_toggle

        super().__init__(pages, **kwargs)

    @override
    def _render(self) -> None:
        super()._render()
        self._toggle_button.label = f"{'Hide' if self.shown else 'Show'} source"
        self._controls.add_item(self._toggle_button)

    @override
    def _disable_controls(self) -> None:
        super()._disable_controls()
        self._toggle_button.disabled = True

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
        self.pages = build_code_pages(
            self.source, self.syntax, self.output, self.failed, self.image_filenames, self.shown
        )
        self.page = 0
        self._render()
        await interaction.response.edit_message(view=self)
