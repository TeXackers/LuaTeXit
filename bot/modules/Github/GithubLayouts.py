"""
Layout construction specific to the Github module.
"""

import re
from typing import TypedDict

import discord
from cmdClient.Layouts import Body, Footer, HeaderWithThumbnail
from discord.ui import Container, LayoutView, MediaGallery, Separator


class AuthorInfo(TypedDict):
    """
    A piecemeal dict version of the [`NamedUser`](https://github.com/PyGithub/PyGithub/blob/main/github/NamedUser.py) class defined by py-github.

    Originally comprising the following:
    ```py
    def _initAttributes(self) -> None:
        self._avatar_url: Attribute[str] = NotSet
        self._bio: Attribute[str | None] = NotSet
        self._blog: Attribute[str | None] = NotSet
        self._business_plus: Attribute[bool] = NotSet
        self._collaborators: Attribute[int] = NotSet
        self._company: Attribute[str | None] = NotSet
        self._contributions: Attribute[int] = NotSet
        self._created_at: Attribute[datetime] = NotSet
        self._disk_usage: Attribute[int] = NotSet
        self._display_login: Attribute[str] = NotSet
        self._email: Attribute[str | None] = NotSet
        self._events_url: Attribute[str] = NotSet
        self._followers: Attribute[int] = NotSet
        self._followers_url: Attribute[str] = NotSet
        self._following: Attribute[int] = NotSet
        self._following_url: Attribute[str] = NotSet
        self._gists_url: Attribute[str] = NotSet
        self._gravatar_id: Attribute[str | None] = NotSet
        self._hireable: Attribute[bool | None] = NotSet
        self._html_url: Attribute[str] = NotSet
        self._id: Attribute[int] = NotSet
        self._invitation_teams_url: Attribute[str] = NotSet
        self._inviter: Attribute[NamedUser] = NotSet
        self._ldap_dn: Attribute[str] = NotSet
        self._location: Attribute[str | None] = NotSet
        self._login: Attribute[str] = NotSet
        self._name: Attribute[str] = NotSet
        self._node_id: Attribute[str] = NotSet
        self._notification_email: Attribute[str] = NotSet
        self._organizations_url: Attribute[str] = NotSet
        self._owned_private_repos: Attribute[int] = NotSet
        self._permissions: Attribute[Permissions] = NotSet
        self._plan: Attribute[Plan] = NotSet
        self._private_gists: Attribute[int] = NotSet
        self._public_gists: Attribute[int] = NotSet
        self._public_repos: Attribute[int] = NotSet
        self._received_events_url: Attribute[str] = NotSet
        self._repos_url: Attribute[str] = NotSet
        self._role: Attribute[str] = NotSet
        self._role_name: Attribute[str] = NotSet
        self._site_admin: Attribute[bool] = NotSet
        self._starred_at: Attribute[str] = NotSet
        self._starred_url: Attribute[str] = NotSet
        self._subscriptions_url: Attribute[str] = NotSet
        self._suspended_at: Attribute[datetime | None] = NotSet
        self._team_count: Attribute[int] = NotSet
        self._text_matches: Attribute[dict[str, Any]] = NotSet
        self._total_private_repos: Attribute[int] = NotSet
        self._twitter_username: Attribute[str | None] = NotSet
        self._two_factor_authentication: Attribute[bool] = NotSet
        self._type: Attribute[str] = NotSet
        self._updated_at: Attribute[datetime] = NotSet
        self._url: Attribute[str] = NotSet
        self._user_view_type: Attribute[str] = NotSet
    ```

    Modify as necessary later down the track.
    """

    name: str
    url: str
    avatar_url: str


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
        author: AuthorInfo,
        created_at,
        footer_text: str,
        images: list[str] | None,
    ) -> None:
        """
        title: The title of the embed, shown in bold at the top of the embed. Can be empty string.

        url: URL for the title, e.g., link to the PR/issue

        description: Main content to be shown.

        colour: Accent colour for the embed.

        author: AuthorInfo with `name`, `url` and `avatar_url` fields, used for `set_author`.
        footer_text: Text to be shown in the footer of the embed. Can be empty string.

        images: List of image URLs to be shown in the embed. Can be None or empty list if no images are to be shown.
        """
        super().__init__(timeout=None)

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

        container = Container(HeaderWithThumbnail(header_text, author["avatar_url"]), Separator(), accent_colour=colour)

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
