"""
Provides typst utility commands.
"""

import random
import re
from datetime import datetime

import aiohttp
import discord
from bs4 import BeautifulSoup
from utils.lib import prop_tabulate

from modules.Tex.latexutil_cmds import MarkdownConverter
from modules.Typst.module import typst_module as module

TYPST_UNIVERSE_URL = "https://typst.app/universe/package/{}"
TYPST_UNIVERSE_SEARCH_DISCIPLINE = "https://typst.app/universe/search?discipline={}"
TYPST_UNIVERSE_SEARCH_CATEGORY = "https://typst.app/universe/search?category={}"


async def typst_soup_site(url: str) -> BeautifulSoup | None:
    async with aiohttp.ClientSession() as session, session.get(url, allow_redirects=False) as response:
        if response.status == 200:
            data = await response.read()
            return BeautifulSoup(data.decode("utf8"), "html.parser")
        print(response.status, response.reason)
        return None


async def get_typst_universe_package_info(soup: BeautifulSoup) -> tuple[str, str, str, list[str], list[str], list[str]]:
    try:
        typst_universe_package_title = soup.find_all("h1")[-1].text
    except AttributeError:
        return ("", "", "", [], [], [])

    c = MarkdownConverter()
    readme_html = str(soup.find("section", id="readme"))
    # this yields UnicodeDecodeError sometimes
    typst_universe_package_desc = c.convert(readme_html)
    while "  " in typst_universe_package_desc:
        typst_universe_package_desc = typst_universe_package_desc.replace("  ", " ")

    typst_universe_package_colour = (
        soup.find_all("div", id="banner")[0].attrs["style"].split(";")[-1].split("#")[1][0:6]
    )

    typst_universe_package_metadata = soup.find_all("dd")
    typst_universe_package_author = typst_universe_package_metadata[0].text.strip()
    typst_universe_package_licence = typst_universe_package_metadata[1].text.strip()
    typst_universe_package_version = typst_universe_package_metadata[2].text.strip()
    typst_universe_package_latest_update = datetime.strptime(
        typst_universe_package_metadata[3].text,
        "%B %d, %Y",
    ).isoformat()[:10]
    typst_universe_package_first_release = datetime.strptime(
        typst_universe_package_metadata[4].text,
        "%B %d, %Y",
    ).isoformat()[:10]
    typst_universe_package_compat = typst_universe_package_metadata[5].text

    category = soup.find_all("dd")[-1].find_all("a")

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
        typst_universe_package_repository_link = typst_universe_package_metadata[7].find("a").attrs["href"]
        typst_universe_package_repository = f"[link]({typst_universe_package_repository_link})"
    except IndexError:
        typst_universe_package_repository_link = ""
        typst_universe_package_repository = ""

    # images
    readme = soup.find("section", id="readme")
    all_images = readme.find_all("img") if readme else []
    all_images = [img for img in all_images if not img.get("alt")]
    image_urls = [img.attrs["src"] for img in all_images]

    field_title, field_value = [], []
    if typst_universe_package_author:
        field_title.append("Author")
        field_value.append(typst_universe_package_author)
    if typst_universe_package_licence:
        field_title.append("Licence")
        field_value.append(typst_universe_package_licence)
    if typst_universe_package_version:
        field_title.append("Version")
        field_value.append(typst_universe_package_version)
    if typst_universe_package_latest_update:
        field_title.append("Last update")
        field_value.append(typst_universe_package_latest_update)
    if typst_universe_package_first_release:
        field_title.append("First release")
        field_value.append(typst_universe_package_first_release)
    if typst_universe_package_compat:
        field_title.append("Typst version")
        field_value.append(typst_universe_package_compat)
    if typst_universe_package_category:
        field_title.append("Category")
        field_value.append(typst_universe_package_category)
    if typst_universe_package_repository:
        field_title.append("Repository")
        field_value.append(typst_universe_package_repository)

    return (
        typst_universe_package_title,
        typst_universe_package_desc,
        typst_universe_package_colour,
        field_value,
        field_title,
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
        field_value,
        field_title,
        image_urls,
    ) = await get_typst_universe_package_info(ttan_soup)

    if not typst_universe_package_title:
        return await ttan_out_msg.edit(content=f"Could not find a package named `{ctx.args}` on Typst Universe.")

    embed_table = ""
    if len(field_value) > 0:
        embed_table = prop_tabulate(field_title, field_value)
    else:
        pass

    find_out_more = (
        f"Find out more at [Typst Universe](https://typst.app/universe/package/{typst_universe_package_title.lower()})."
    )

    # description
    if len(typst_universe_package_desc) > 400:
        desc = typst_universe_package_desc[:400]
        r_newline = desc.rfind("\n")
        r_space = desc.rfind(" ")
        desc = desc[: max(r_space, r_newline)] + "..."

    # handle big tables
    if len(embed_table) > 700:
        embed_table = embed_table[:700]
        rightmost_newline = embed_table.rfind("\n")
        embed_table = embed_table[: rightmost_newline + 1]
    embed_description = desc + "\n\n" + embed_table + "\n" + find_out_more

    ttan_embed = discord.Embed(
        title=typst_universe_package_title,
        url=ttan_url,
        description=embed_description,
        color=int(typst_universe_package_colour, 16),
    )

    # randomly select one as embed image
    if image_urls:
        img_url = random.choice(image_urls)
        ttan_embed.set_image(url=img_url)

    return await ttan_out_msg.edit(content="", embed=ttan_embed)
