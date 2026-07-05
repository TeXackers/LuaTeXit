"""
Layout construction specific to the Github module.
"""

import re

import discord
from cmdClient.Layouts import Body, Footer, HeaderWithThumbnail
from discord.ui import Container, LayoutView, MediaGallery, Separator


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
        created_at,
        footer_text: str,
        images: list[str] | None,
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

        # check that created_at can be parsed by discord.utils.format_dt
        try:
            discord.utils.format_dt(created_at, "R")
        except Exception as e:
            raise ValueError("created_at must be a datetime object or a string in ISO format") from e

        created = discord.utils.format_dt(created_at, "R")

        # Header
        match url, author["url"]:
            case (None, None):
                header_text = f"{title} ({created})\n{author['name']}"
            case (None, _):
                header_text = f"{title} ({created})\n[{author['name']}]({author['url']})"
            case (_, None):
                header_text = f"[{title}]({url}) ({created})\n{author['name']}"
            case (_, _):
                header_text = f"[{title}]({url}) ({created})\n[{author['name']}]({author['url']})"

        container = Container(HeaderWithThumbnail(header_text, author["icon_url"]), Separator(), accent_colour=colour)

        # description is already sanitised so we just need to look for a URL that ends with a common image extension, then replace it with the actual image as a media gallery item, and split the description into blocks accordingly. We can assume that the image URLs are on their own line, as is the case for Github markdown.
        # Exception is: https://github.com/user-attachments/assets/ followed by hash hex (with no image extension) - these are used by Github for images uploaded directly to the issue/PR and still need to be rendered as images.
        github_image_patterns = re.compile(
            r"(https?://\S+\.(?:jpg|jpeg|png|gif|bmp|webp|svg)(?:\?\S*)?|https?://github\.com/user-attachments/assets/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            re.IGNORECASE,
        )

        description_blocks = re.split(github_image_patterns, description)
        # r"\n(?=\s*(?:https?:\/\/user-attachments\.githubusercontent\.com\/assets\/[a-f0-9]+))",

        if len(description_blocks) == 1:
            # format double \n as single \n
            description = description.replace("\n\n", "\n")
            container.add_item(Body(description))
        else:
            for i, block in enumerate(description_blocks):
                if block.strip():  # only add non-empty blocks
                    # remove the image URL from the block if it exists, as it will be shown in the media gallery
                    block = re.sub(github_image_patterns, "", block)
                    if block:
                        # at this stage, there's some text to render
                        block = block.replace("\n\n", "\n")
                        # remove leading and trailing whitespace/newlines
                        block = block.strip()
                        container.add_item(Body(block))

                if images and i < len(images):  # add image after the block, if it exists
                    container.add_item(MediaGallery(discord.MediaGalleryItem(images[i])))

        # add the rest
        container.add_item(Separator())
        container.add_item(Footer(footer_text))

        self.add_item(container)
