import asyncio
import random
import re
import urllib.parse
from asyncio.subprocess import PIPE

import discord
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from cmdClient import Context  # noqa
from cmdClient.Format import bf, footnote
from cmdClient.Layouts import GenericFullEmbed
from iso639 import Language, LanguageNotFoundError
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


async def soup_site(url: str) -> BeautifulSoup:
    async with ClientSession() as session, session.get(url, timeout=ClientTimeout(total=10)) as r:
        text = await r.text()
    return BeautifulSoup(text, "html.parser")


line_beginning_re = re.compile(r"^", re.MULTILINE)
whitespace_re = re.compile(r"[\r\n\s\t ]+")


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
        return self.process_tag(soup)

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
        return f"{text}" if text else ""

    def convert_strong(self, el, text: str) -> str:
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        return f"{prefix}**{text}**{suffix}"


def search_n_parse(soup: BeautifulSoup) -> tuple[str, str, list[str], list[str]]:
    title = soup.find("h1")

    if title and title.contents and "Not Found" in str(title.contents[0]):
        return ("", "", [], [])

    try:
        if title and title.contents and len(title.contents) > 2 and "is Gone" in str(title.contents[2]):
            div = soup.find("div", attrs={"class": "left"})
            desc = div.text
            return (title.text, desc, [], [])
    except IndexError:
        pass

    title = title.text
    converter = MarkdownConverter()
    package_desc = soup.find("p")
    emb_desc = converter.process_tag(package_desc)

    table = soup.find("table")
    prop_list = []
    value_list = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        ignored = ["TDS archive", "Licenses", "Copyright", "Maintainer"]
        if tds[0].text in ignored:
            continue

        brs = tds[1].find_all("br")
        if brs is not None:
            for _ in brs:
                tds[1].br.replace_with(", ")

        links = tds[1].find_all("a")
        if links:
            for link in links:
                if tds[0].text == "Documentation":
                    link.insert_after(", ")
                if link.text == urllib.parse.urljoin(ctan_url, link.attrs["href"]):
                    md_link = link.text
                else:
                    md_link = "[{}]({})".format(link.text, urllib.parse.urljoin(ctan_url, link.attrs["href"]))
                tds[1].a.replace_with(md_link)

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
    out_msg = await ctx.reply(
        f"Searching the texdoc database, please wait... {ctx.client.conf.emojis.getemoji('loading')}",
    )
    if len(ctx.args) > 800:
        await out_msg.delete()
        return await ctx.error_reply("Given query is too long!")
    if not ctx.args:
        await out_msg.delete()
        return await ctx.error_reply("Please give me something to search for!")
    # ping to check if it exists
    addr: str = texdoc_url.format(urllib.parse.quote_plus(ctx.args))
    async with ClientSession() as session, session.get(addr, timeout=ClientTimeout(total=10)) as page:
        status = page.status
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

    loading_emoji = ctx.client.conf.emojis.getemoji("loading")
    out_msg = await ctx.reply(f"Searching the CTAN, please wait... {loading_emoji}")

    soup: BeautifulSoup = soup_site(url)
    title, desc, prop_list, value_list = search_n_parse(soup)

    if ctx.alias.lower() == "ctans":
        result_url = search_url.format(urllib.parse.quote_plus(ctx.args))
        soup = soup_site(result_url)
        desc = f"From {result_url}"
        if title:
            desc += f"\nDirect page found at [{ctx.args}]({url})"
        search_title = soup.find("h1").text
        embed = discord.Embed(title=search_title, description=desc)
        stats = soup.find("p").text
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
            if url.text == urllib.parse.urljoin(ctan_url, url.attrs["href"]):
                md_link = url.text
            else:
                md_link = "[{}]({})".format(url.text, urllib.parse.urljoin(ctan_url, url.attrs["href"]))
            md_links.append(md_link)
        field_value = "\n".join(md_links)
        embed.add_field(name=stats, value=field_value)
        return await out_msg.edit(content="", embed=embed)

    if not title:
        return await out_msg.edit(content=f"I couldn't find a package named `{ctx.args}`!")

    table = tabulate(dict(zip(prop_list, value_list, strict=True))) if prop_list else ""
    read_more = f"Read more at [CTAN page]({url}) of the package."
    if len(desc) > 700:
        desc = desc[:700]
        r_newline = desc.rfind("\n")
        r_space = desc.rfind(" ")
        desc = desc[: max(r_newline, r_space)] + "..."
    if len(table) > 900:
        table = table[:900]
        rightmost_newline = table.rfind("\n")
        table = table[: rightmost_newline + 1]
    emb_desc = desc + "\n" + table

    v = GenericFullEmbed(
        header=title,
        body=emb_desc,
        footer=read_more,
        thumbnail_url=random.choice(thumbnails),
        accent_colour=discord.Colour.from_rgb(66, 66, 133),
    )

    # embed = discord.Embed(
    #     title=title,
    #     url=url,
    #     description=emb_desc,
    #     color=discord.Color.from_rgb(66, 66, 133),  # ctan's #424285 color
    # )
    # randomly choose url from thumbnail list

    return await out_msg.edit(content="", view=v)


def glyph_or_unicode(arg: str) -> list[str] | None:
    """
    Purpose: Making four or five digit to be used in `:charset` for fc-list.

    Parse the input and determine if it is a unicode or a glyph.
    If it's a glyph, then convert it to its unicode hex value.
    The final output is a string containing a four (preferred) or five-letter unicode hex value.
    Remove any U+ as fontconfig doesn't need it.
    """
    if not arg:
        raise ValueError("Argument cannot be empty.")

    # if space or comma in arg, split it
    if "," in arg:
        argstack: list[str] = arg.split(",")
    else:
        argstack: list[str] = [arg]
    output: list[str] = []

    for a in argstack:
        a = a.strip().lower().lstrip("u+")

        # User enters glyph(s)
        if len(a) == 1:
            # It's a glyph
            output.append(f"{ord(a):05x}")

        # User enters unicode(s)
        elif len(a) > 1:
            a_test = f"{a:0>5}"
            # Is it unicode? Each letter must be between 0-9 or a-f
            if all(c in "0123456789abcdef" for c in a_test):
                # also ensure that the hex value is no greater than 1FA6D
                if int(a_test, 16) <= 0x1FA6D:
                    output.append(a_test)
                else:
                    output.append(None)
            else:
                output.append(None)
        else:
            output.append(None)

    return [o for o in output if o is not None]


def clean_md(text: str) -> str:
    """
    Cleans up markdown text by removing unnecessary whitespace and formatting.
    """
    if not text:
        return ""
    # remove all markdown formatting things, i.e. <>!@#$%^&*()_+-=~`[]{}|;:'",.<>?/
    text = re.sub(r"[<>!@#$%^&*()_+\-=\~`[\]{}|;:'\",.<>?/]", "", text)
    # remove all whitespace characters, i.e. \n, \r, \t, space
    text = re.sub(r"[\n\r\t ]+", " ", text)
    return text.strip()


@module.cmd(
    "findfont",
    desc="Looks for fonts supporting a given argument",
    aliases=["fc"],
    flags=["char==", "lang==", "name=="],
)
async def cmd_findfont(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}findfont <feature>
    Description:
        Search for fonts in LuaTeXit's system for a given feature or features.
    Examples``:
        {prefix}findfont --lang <iso639 | name>
        {prefix}findfont --char <unicode hex code | glyph(s)>
        {prefix}findfont --name <pattern>
    """
    fclist_chars: str = ""
    fclist_lang: str = ""
    params_dict: dict = {"query": None, "type": None}
    out_msg = await ctx.reply(f"Searching for fonts, please wait... {ctx.client.conf.emojis.getemoji('loading')}")

    if flags["char"]:
        requested_chars = glyph_or_unicode(clean_md(flags["char"]))
        if not requested_chars:
            await out_msg.delete()
            return await ctx.error_reply("Invalid unicode or glyph(s).")
        if len(requested_chars) > 1:
            fclist_chars = ":charset=" + ",".join(requested_chars)
            params_dict["Characters"] = ", ".join(requested_chars)
        elif len(requested_chars) == 1:
            fclist_chars = ":charset=" + str(requested_chars[0])
            params_dict["Characters"] = str(requested_chars[0])
        else:
            await out_msg.delete()
            ctx.log(f"Requested characters: {requested_chars}", context="findfont")
            return await ctx.error_reply("Something went wrong while processing the characters.")

        params_dict["query"] = clean_md(flags["char"])
        params_dict["type"] = "character" if len(requested_chars) == 1 else "characters"

    if flags["lang"]:
        requested_language: Language
        if len(flags["lang"]) > 3:
            try:
                requested_language = Language.match(clean_md(flags["lang"]).capitalize())
            except LanguageNotFoundError:
                await out_msg.delete()
                return await ctx.error_reply("Invalid language code.")
        else:
            try:
                requested_language = Language.match(clean_md(flags["lang"]).lower())
            except LanguageNotFoundError:
                await out_msg.delete()
                return await ctx.error_reply("Invalid language code.")

        params_dict["query"] = requested_language.name
        params_dict["type"] = "language"

        fclist_lang: str = ":lang=" + str(requested_language.part1 or requested_language.part2t)

    findfont_cmd = ["fc-list", f"{fclist_chars}{fclist_lang}", ":", "family"]

    proc = await asyncio.create_subprocess_exec(*findfont_cmd, stdout=PIPE, stderr=PIPE)
    fc_out, fc_err = await proc.communicate()

    # Error out early
    if fc_err:
        await out_msg.delete()
        return await ctx.error_reply(f"{fc_err.decode('utf-8')}")

    fc_out = fc_out.decode("utf-8").split("\n")

    if not fc_out:
        await out_msg.delete()
        return await ctx.error_reply("No fonts found.")

    # Remove fonts that start with `.`
    fc_out_preprocessed = [line.replace("\\", "") for line in fc_out if not line.startswith(".")]
    # Split by `,` and only grab the first element
    fc_out_preprocessed = [line.split(",")[0].strip() for line in fc_out_preprocessed]

    if flags["name"]:
        params_dict["query"] = clean_md(flags["name"])
        params_dict["type"] = "name"
        fc_out_preprocessed = [
            f.title() for f in [f.lower() for f in fc_out_preprocessed] if clean_md(flags["name"]).lower() in f
        ]
        if not fc_out_preprocessed:
            await out_msg.delete()
            return await ctx.error_reply(f"No fonts found matching the name:\n\n{bf(clean_md(flags['name']))}.")

    fc_out_sorted: list[str] = sorted(set(fc_out_preprocessed))
    fc_out: list[str] = [f for f in fc_out_sorted if f]
    footnote_text = (
        f"searching for {bf(params_dict['query'])} by {bf(params_dict['type'])}"
        if params_dict["query"] and params_dict["type"]
        else "Showing all fonts"
    )
    title_text = (
        f"Font query ({len(fc_out)} results)\n{footnote(footnote_text)}"
        if flags
        else f"Font query ({len(fc_out)} results)"
    )

    await out_msg.delete()
    return await ctx.pager_v2(content=fc_out, title=title_text, code=True, maxheight=25)
