"""
Provides typst utility commands.
"""

import random
import re
from datetime import datetime, timezone

import aiohttp
import discord
from bs4 import BeautifulSoup
from cmdClient.Layouts import Body, Footer, Header
from discord.ui import Container, LayoutView, MediaGallery, Separator
from utils.cache import async_ttl_cache
from utils.lib import tabulate

from modules.Tex.latexutil_cmds import MarkdownConverter
from modules.Typst.module import typst_module as module

TYPST_UNIVERSE_URL = "https://typst.app/universe/package/{}"
TYPST_UNIVERSE_SEARCH_DISCIPLINE = "https://typst.app/universe/search?discipline={}"
TYPST_UNIVERSE_SEARCH_CATEGORY = "https://typst.app/universe/search?category={}"


@async_ttl_cache(hours=24)
async def typst_soup_site(url: str) -> BeautifulSoup | None:
    async with aiohttp.ClientSession() as session, session.get(url, allow_redirects=False) as response:
        if response.status == 200:
            data = await response.read()
            return BeautifulSoup(data.decode("utf8"), "html.parser")
        return None


async def get_typst_universe_package_info(soup: BeautifulSoup) -> tuple[str, str, str, dict[str, str], list[str]]:
    try:
        typst_universe_package_title = soup.find_all("h1")[-1].text
    except AttributeError:
        return ("", "", "", {}, [])

    c = MarkdownConverter()
    readme_html = str(soup.find("section", id="readme"))
    # this yields UnicodeDecodeError sometimes
    typst_universe_package_desc = c.convert(readme_html)
    while "  " in typst_universe_package_desc:
        typst_universe_package_desc = typst_universe_package_desc.replace("  ", " ")

    typst_universe_package_colour = (
        soup.find_all("div", id="banner")[0].attrs["style"].split(";")[-1].split("#")[1][0:6]
    )

    def relative_date(text: str) -> str:
        return discord.utils.format_dt(datetime.strptime(text, "%B %d, %Y").replace(tzinfo=timezone.utc), "R")

    metadata = soup.find_all("dd")
    typst_universe_package_author = metadata[0].text.strip()
    typst_universe_package_licence = metadata[1].text.strip()
    typst_universe_package_version = metadata[2].text.strip()
    typst_universe_package_latest_update = relative_date(metadata[3].text)
    typst_universe_package_first_release = relative_date(metadata[4].text)
    typst_universe_package_compat = metadata[5].text

    category = metadata[-1].find_all("a")

    category_links = []
    typst_universe_package_category = ""
    if len(category) == 1:
        typst_universe_package_category = f"[{category[0].text.strip()}](https://typst.app/universe/search?category={category[0].text.strip().lower()})"
    elif len(category) > 1:
        for cat in category:
            cat_link = f"[{cat.text.strip()}](https://typst.app/universe/search?category={cat.text.strip().lower()})"
            category_links.append(cat_link)
        typst_universe_package_category = ", ".join(category_links)

    try:
        typst_universe_package_repository_link = metadata[7].find("a").attrs["href"]
        typst_universe_package_repository = f"[link]({typst_universe_package_repository_link})"
    except IndexError:
        typst_universe_package_repository = ""

    # images (svg isn't renderable by Discord's MediaGallery, so exclude those)
    readme = soup.find("section", id="readme")
    all_images = readme.find_all("img") if readme else []
    all_images = [img for img in all_images if not img.get("alt")]
    image_urls = [
        img.attrs["src"] for img in all_images if not img.attrs["src"].split("?")[0].lower().endswith(".svg")
    ]

    raw_fields = {
        "Author": typst_universe_package_author,
        "Licence": typst_universe_package_licence,
        "Version": typst_universe_package_version,
        "First release": typst_universe_package_first_release,
        "Last update": typst_universe_package_latest_update,
        "Typst version": typst_universe_package_compat,
        "Category": typst_universe_package_category,
        "Repository": typst_universe_package_repository,
    }
    fields = {title: value for title, value in raw_fields.items() if value}

    return (
        typst_universe_package_title,
        typst_universe_package_desc,
        typst_universe_package_colour,
        fields,
        image_urls,
    )


@module.cmd(
    "typst-universe",
    desc="Look up a package on the [Typst Universe](https://typst.app/universe/).",
    aliases=["ttan", "tuni", "tu"],
)
async def cmd_typst_universe(ctx):
    """
    Usage``:
        {prefix}typst-universe <package-name>
    Description:
        Looks up a package on the [Typst Universe](https://typst.app/universe/) and returns its information.
    Examples``:
        {prefix}typst-universe cetz
        {prefix}ttan polylux
        {prefix}tu touying
    """
    # all packages have hyphens instead of spaces

    ttan_url = TYPST_UNIVERSE_URL.format(ctx.args.replace(" ", "-"))

    # complain if nothing given
    if not ctx.args:
        return await ctx.error_reply("Please provide a package name to look up.")

    # complain if invalid package name
    if not re.sub(r"[-.]", "", ctx.args).isalnum():
        return await ctx.error_reply(f"`{ctx.args}` is not a valid package name!")

    # complain if too long
    if len(ttan_url) > 1000:
        return await ctx.error_reply("The generated URL is too long to be sent.")

    # righto, let's send the URL
    loading_emoji = ctx.client.conf.emojis.getemoji("loading")
    ttan_out_msg = await ctx.reply(f"Looking up Typst Universe. Please wait... {loading_emoji}")

    ttan_soup = await typst_soup_site(ttan_url)

    (
        typst_universe_package_title,
        typst_universe_package_desc,
        typst_universe_package_colour,
        fields,
        image_urls,
    ) = await get_typst_universe_package_info(ttan_soup)

    if not typst_universe_package_title:
        return await ttan_out_msg.edit(content=f"Could not find a package named `{ctx.args}` on Typst Universe.")

    embed_table = tabulate(fields) if fields else ""

    find_out_more = (
        f"Find out more at [Typst Universe](https://typst.app/universe/package/{typst_universe_package_title.lower()})."
    )

    # description
    desc = typst_universe_package_desc
    if len(desc) > 1000:
        desc = desc[:1000]
        r_newline = desc.rfind("\n")
        r_space = desc.rfind(" ")
        desc = desc[: max(r_space, r_newline)] + "..."

    # handle big tables
    if len(embed_table) > 1000:
        embed_table = embed_table[:1000]
        rightmost_newline = embed_table.rfind("\n")
        embed_table = embed_table[: rightmost_newline + 1]

    container = Container(accent_colour=discord.Colour(int(typst_universe_package_colour, 16)))

    container.add_item(Header(typst_universe_package_title, 1))
    container.add_item(Separator())
    if desc:
        container.add_item(Body(desc))
    if embed_table:
        container.add_item(Body(embed_table))
    container.add_item(Footer(find_out_more))
    # randomly select one as embed image
    if image_urls:
        container.add_item(MediaGallery(discord.MediaGalleryItem(random.choice(image_urls))))

    v = LayoutView()
    v.add_item(container)

    return await ttan_out_msg.edit(content="", view=v)
