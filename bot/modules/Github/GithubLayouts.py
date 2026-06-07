"""
Layout construction specific to the Github module.
"""

import discord
from discord.ui import Separator
from discord.ui import MediaGallery
from discord.ui import LayoutView
from discord.ui import TextDisplay
from discord.ui import Container
from discord.ui import Section
from discord.ui import Thumbnail


class Header(TextDisplay):
    def __init__(self, text: str) -> None:
        super().__init__(f"### {text}")


class HeaderWithThumbnail(Section):
    def __init__(self, text: str, thumbnail_url: str) -> None:
        super().__init__(
            Header(text),
            accessory=Thumbnail(thumbnail_url),
        )


class Body(TextDisplay):
    def __init__(self, text: str) -> None:
        super().__init__(f"\n{text}\n")


class Footer(TextDisplay):
    def __init__(self, text: str) -> None:
        super().__init__(f"\n-# {text}")


class SectionWithThumbnail(Section):
    def __init__(self, text: str, thumbnail_url: str) -> None:
        super().__init__(
            Body(text),
            accessory=Thumbnail(thumbnail_url),
        )


class GithubEmbed(LayoutView):
    """
    Layout for Github embeds.

    Generally follows similar format as discord.Embed.
    """

    def __init__(
        self,
        title: str,
        url: str,
        description: str,
        colour: discord.Color,
        author: dict[str, str],
        footer_text: str,
        images: list[str] | None = None,
    ) -> None:
        """
        title: The title of the embed, shown in bold at the top of the embed. Can be empty string.

        url: URL for the title, e.g., link to the PR/issue

        description: Main content to be shown.

        colour: Accent colour for the embed.

        author: dict containing `set_author` fields. Must have `name`, `url` and `icon_url` keys.
        footer_text: Text to be shown in the footer of the embed. Can be empty string.

        images: List of image URLs to be shown in the embed. Can be None or empty list if no images are to be shown.
        """
        super().__init__(timeout=None)

        # check that author dict has required keys
        if not all(k in author for k in ("name", "url", "icon_url")):
            raise ValueError("Author dict must have 'name', 'url' and 'icon_url' keys")

        # Header
        match url, author["url"]:
            case (None, None):
                header_text = f"{title}\n{author['name']}"
            case (None, _):
                header_text = f"{title}\n[{author['name']}]({author['url']})"
            case (_, None):
                header_text = f"[{title}]({url})\n{author['name']}"
            case (_, _):
                header_text = f"[{title}]({url})\n[{author['name']}]({author['url']})"

        container = Container(
            HeaderWithThumbnail(header_text, author["icon_url"]),
            Separator(),
            Body(description),
            Separator(),
            Footer(footer_text),
            accent_colour=colour,
        )
        self.add_item(container)
        if images and len(images) == 1:
            self.add_item(MediaGallery(discord.MediaGalleryItem(images[0])))
        elif images and len(images) > 1:
            for img_link in images:
                self.add_item(MediaGallery(discord.MediaGalleryItem(img_link)))
