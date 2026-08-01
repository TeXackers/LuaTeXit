import random
import re
import urllib.parse
from typing import cast

import discord
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from cmdClient import Context
from cmdClient.Layouts import TextEmbed
from utils.cache import async_ttl_cache
from utils.interactive import get_application_emoji_by_name
from utils.lib import tabulate

from .module import latex_module as module

"""
Provides ctan and texdoc commands.
"""

texdoc_url: str = "http://texdoc.net/pkg/{}"
ctan_url: str = "https://ctan.org/{}"
lion_url: str = "https://ctan.org/lion/files/ctan_lion_350x350.png"
bend_url: str = "https://cdn.discordapp.com/attachments/1043075521476579398/1043077445911322624/dangerous-bend.png"

thumbnails = [lion_url, bend_url]


@async_ttl_cache(days=7)
async def soup_site(url: str) -> BeautifulSoup:
    async with ClientSession() as session, session.get(url, timeout=ClientTimeout(total=10)) as r:
        text = await r.text()
    return BeautifulSoup(text, "html.parser")


@async_ttl_cache(days=7)
async def texdoc_status(pkg_name: str) -> int:
    """Check whether `pkg_name` has a texdoc.net page, caching the result since it rarely changes."""
    addr = texdoc_url.format(urllib.parse.quote_plus(pkg_name))
    async with ClientSession() as session, session.get(addr, timeout=ClientTimeout(total=10)) as page:
        return page.status


line_beginning_re = re.compile(r"^", re.MULTILINE)
whitespace_re = re.compile(r"[\r\n\s\t ]+")
whitespace_around_newline_re = re.compile(r"[ \t]*\n[ \t]*")


def escape(text: str) -> str:
    if not text:
        return ""
    return text.replace("_", r"\_")


def chomp(text: str) -> tuple[str, str, str]:
    """
    If the text in an inline tag like b, a, or em contains a leading or trailing
    space, strip the string and return a space as suffix of prefix, if needed.
    This function is used to prevent conversions like
        <b> foo</b> => ** foo**
    """
    prefix = " " if text and text[0] == " " else ""
    suffix = " " if text and text[-1] == " " else ""
    text = text.strip()
    return (prefix, suffix, text)


class MarkdownConverter:
    def __init__(self):
        self.bullets = "-+*"

    def convert(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return self.convert_node(soup)

    def convert_node(self, node) -> str:
        """Like process_tag, but also cleans up whitespace left around paragraph breaks."""
        text = self.process_tag(node)
        return whitespace_around_newline_re.sub("\n", text).strip()

    def process_tag(self, node) -> str:
        text = ""
        # markdown headings can't include block elements (elements w/newlines)

        # Convert the children first
        for el in node.children:
            if isinstance(el, NavigableString):
                text += self.process_text(str(el))
            else:
                text += self.process_tag(el)

        convert_fn = getattr(self, f"convert_{node.name}", None)
        if convert_fn:
            text = convert_fn(node, text)

        return text

    @staticmethod
    def process_text(text: str) -> str:
        return escape(whitespace_re.sub(" ", text or ""))

    @staticmethod
    def indent(text: str, level: int) -> str:
        return line_beginning_re.sub("\t" * level, text) if text else ""

    @staticmethod
    def underline(text: str, pad_char: str) -> str:
        text_strip: str = (text or "").rstrip()
        return f"{text_strip}\n{pad_char * len(text_strip)}\n\n" if text_strip else ""

    def convert_a(self, el, text: str) -> str:
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        href = urllib.parse.urljoin(ctan_url, el.get("href"))
        title = el.get("title")
        # For the replacement see #29: text nodes underscores are escaped
        title_part = f' "{title.replace('"', r'\\"')}"' if title else ""
        return f"{prefix}[{text}]({href}{title_part}){suffix}" if href else text

    def convert_b(self, el, text: str) -> str:
        return self.convert_strong(el, text)

    def convert_span(self, el, text: str) -> str:
        return f"{text}" if text else ""

    def convert_blockquote(self, el, text) -> str:
        return f"\n{line_beginning_re.sub('> ', text)}" if text else ""

    def convert_br(self, el, text) -> str:
        return "  \n"

    def convert_em(self, el, text: str) -> str:
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        return f"{prefix}*{text}*{suffix}"

    def convert_i(self, el, text):
        return self.convert_em(el, text)

    def convert_list(self, el, text):

        # Converting a list to inline is undefined.
        # Ignoring convert_to_inline for list.

        nested = False
        while el:
            if el.name == "li":
                nested = True
                break
            el = el.parent
        if nested:
            # remove trailing newline if nested
            return "\n" + self.indent(text, 1).rstrip()
        return "\n" + text

    convert_ul = convert_list
    convert_ol = convert_list

    def convert_li(self, el, text):
        parent = el.parent
        if parent is not None and parent.name == "ol":
            start = int(parent.get("start", 1)) if parent.get("start") else 1
            bullet = "%s." % (start + parent.index(el))
        else:
            depth = -1
            while el:
                if el.name == "ul":
                    depth += 1
                el = el.parent
            bullets = self.bullets
            bullet = self.bullets[depth % len(bullets)]
        return f"{bullet} {text or ''}\n"

    def convert_p(self, el, text: str) -> str:
        text = text.strip()
        return f"{text}\n\n" if text else ""

    def convert_strong(self, el, text: str) -> str:
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        return f"{prefix}**{text}**{suffix}"


def search_n_parse(soup: BeautifulSoup) -> tuple[str, str, list[str], list[str]]:
    title = soup.find("h1")

    if title is None:
        return ("", "", [], [])

    if title.contents and "Not Found" in str(title.contents[0]):
        return ("", "", [], [])

    try:
        if title.contents and len(title.contents) > 2 and "is Gone" in str(title.contents[2]):
            div = soup.find("div", attrs={"class": "left"})
            desc = div.text if div else ""
            return (title.text, desc, [], [])
    except IndexError:
        pass

    title = title.text
    converter = MarkdownConverter()
    package_desc = soup.find("p")
    emb_desc = converter.convert_node(package_desc)

    table = soup.find("table")
    prop_list = []
    value_list = []
    if table is None:
        return (title, emb_desc, prop_list, value_list)
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        ignored = ["TDS archive", "Licenses", "Copyright", "Maintainer"]
        if tds[0].text in ignored:
            continue

        for br in tds[1].find_all("br"):
            br.replace_with(", ")

        links = tds[1].find_all("a")
        if links:
            for link in links:
                href = cast("str", link.attrs["href"])
                if tds[0].text == "Documentation":
                    link.insert_after(", ")
                if link.text == urllib.parse.urljoin(ctan_url, href):
                    md_link = link.text
                else:
                    md_link = f"[{link.text}]({urllib.parse.urljoin(ctan_url, href)})"
                link.replace_with(md_link)

        prop_list.append(tds[0].text)
        value_list.append(tds[1].text.rstrip(", "))

    return (title, emb_desc, prop_list, value_list)


@module.cmd("texdoc", desc="Searches the [texdoc](http://texdoc.net)", aliases=["td"])
async def cmd_texdoc(ctx: Context):
    """
    Usage``:
        {prefix}texdoc <package_name>
    Description:
        Gives a link to the documentation of `package_name` from [texdoc](http://texdoc.net).
    Examples``:
        {prefix}texdoc tikz
    """
    loading = await get_application_emoji_by_name(ctx.client, "loading")
    out_msg = await ctx.reply(
        f"Searching the texdoc database, please wait... {loading}",
    )
    if len(ctx.args) > 800:
        await out_msg.delete()
        return await ctx.error_reply("Given query is too long!")
    if not ctx.args:
        await out_msg.delete()
        return await ctx.error_reply("Please give me something to search for!")
    # ping to check if it exists
    status = await texdoc_status(ctx.args)
    if status == 404:
        await out_msg.delete()
        return await ctx.error_reply(f"I couldn't find `{ctx.args}` in the texdoc database!")

    await out_msg.delete()
    return await ctx.reply(f"Documentation for `{ctx.args}`: {texdoc_url.format(urllib.parse.quote_plus(ctx.args))}")


@module.cmd("ctan", desc="Searches the [ctan](https://ctan.org)", aliases=["ctanlink", "ctans"])
async def cmd_ctan(ctx: Context):
    """
    Usage``:
        {prefix}ctan <package_name>
        {prefix}ctans <query>
        {prefix}ctanlink [package_name]
    Description:
        If used as ctan, finds the `package_name` from [ctan](https://ctan.org) and sends the parsed results.

        If used as ctans, searches the ctan, and displays first 10 results.

        If used as ctanlink, provides the direct link to the ctan page with given name of package.
        This does not check whether the page exists.
    Examples``:
        {prefix}ctanlink keyval
        {prefix}ctan amsmath
        {prefix}ctans tables
    """
    url = ctan_url.format(f"pkg/{urllib.parse.quote_plus(ctx.args)}")
    search_url = ctan_url.format("search?phrase={}&max=10")
    if len(url) > 1500:
        return await ctx.error_reply("Given query is too long!")

    if ctx.alias.lower() == "ctanlink":
        return await ctx.reply(url if ctx.args else ctan_url.format(""))

    if not ctx.args:
        return await ctx.error_reply("Please give me something to search for!")
    # remove special characters but hyphens,underscores,dots from package name
    # special characters make ctan redirect to some non-relevant page
    # e.g `:E` for packages start with an E
    # but we allow hyphens,underscores,dots to be in there because they can be
    # used in a package name
    if not re.sub(r"[-_.]", "", ctx.args).isalnum():
        return await ctx.error_reply(f"`{ctx.args}` is not a valid package name!")

    loading = await get_application_emoji_by_name(ctx.client, "loading")
    out_msg = await ctx.reply(f"Searching the CTAN, please wait... {loading}")

    soup: BeautifulSoup = await soup_site(url)
    title, desc, prop_list, value_list = search_n_parse(soup)

    if ctx.alias.lower() == "ctans":
        result_url = search_url.format(urllib.parse.quote_plus(ctx.args))
        soup = await soup_site(result_url)
        desc = f"From {result_url}"
        if title:
            desc += f"\nDirect page found at [{ctx.args}]({url})"
        h1 = soup.find("h1")
        search_title = h1.text if h1 else ""
        embed = discord.Embed(title=search_title, description=desc)
        p = soup.find("p")
        stats = p.text if p else ""
        if "no matching" in stats:
            # shows up when you search for unexpected chars, i.e. `[]`
            idx = stats.rfind("You have")
            if idx != -1:
                stats = stats[:idx].strip()

            embed.add_field(name="No results found!", value=stats)
            return await out_msg.edit(content="", embed=embed)

        urls = soup.find_all("a", attrs={"class": "hit-type-pkg"})
        md_links = []
        for url in urls:
            href = cast("str", url.attrs["href"])
            if url.text == urllib.parse.urljoin(ctan_url, href):
                md_link = url.text
            else:
                md_link = f"[{url.text}]({urllib.parse.urljoin(ctan_url, href)})"
            md_links.append(md_link)
        field_value = "\n".join(md_links)
        embed.add_field(name=stats, value=field_value)
        return await out_msg.edit(content="", embed=embed)

    if not title:
        return await out_msg.edit(content=f"I couldn't find a package named `{ctx.args}`!")

    table = tabulate(dict(zip(prop_list, value_list, strict=True))) if prop_list else ""
    read_more = f"Read more at [CTAN page]({url}) of the package."
    if len(desc) > 1000:
        desc = desc[:1000]
    if len(table) > 900:
        table = table[:900]
        rightmost_newline = table.rfind("\n")
        table = table[: rightmost_newline + 1]
    emb_desc = desc + "\n" + table

    v = TextEmbed(
        header=title,
        body=emb_desc,
        footer=read_more,
        accent_colour=discord.Colour.from_rgb(66, 66, 133),
    )

    return await out_msg.edit(content="", view=v)
