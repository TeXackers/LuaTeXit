"""
Wolfram Alpha command implementation.
"""

import json
import logging
import time
from urllib import parse

import aiohttp
import discord
from cmdClient import Context  # noqa
from cmdClient.Format import bf
from cmdClient.Layouts import Body, Footer, Header
from constants import LuaTeXitCC
from discord.ui import Container, MediaGallery, Separator

from . import wolf_data
from .module import maths_module as module
from .wolf_layouts import MORE_EMOJI, TeaserPagerView

ENDPOINT = "http://api.wolframalpha.com/v2/query?"
WEB = "https://www.wolframalpha.com/"

DEFAULT_SEMATIC_LOCATION: str = parse.quote_plus("Melbourne, Australia")
DEFAULT_LONGLAT: str = "-37.840935,144.946457"
DEFAULT_IP_ADDR: str = "127.0.0.1"
DEFAULT_MAG_SIZE: float = 1
DEFAULT_WIDTH: int = 600


# Detailed error handling when Wolfram's API breaks
class WolframAPIError(Exception):
    def __init__(self, desc, err_msg):
        super().__init__(desc)
        self.err_msg = err_msg


APIErrorDesc = """
               Failed to receive a valid response from Wolfram Alpha's API.
               This service is most likely unavailable.
               Please check Wolfram Alpha's website for status updates.
               """


def build_web_url(query: str) -> str:
    """
    Returns the url for Wolfram Alpha search for this query.
    """
    return "{}input/?i={}".format(WEB, parse.quote_plus(query, safe=""))


async def get_query(query: str, appid: str, **kwargs) -> dict | None:
    """
    Fetches the provided query from the Wolfram Alpha computation engine.
    Has a set of default arguments for the query.
    Any keyword arguments will over-write the defaults.
    Returns the response as a dictionary, or None if the query failed.
    Arguments:
        query: The query to post.
        appid: The Wolfram Appid to use in the query.
        kwargs: Params for the query.
    Returns:
        Dictionary containing results or None if an http error occured.
    """
    # build the full url
    query_url: str = (
        f"{ENDPOINT}appid={appid}&input={parse.quote_plus(query)}"
        "&output=json&units=metric"
        f"&mag={DEFAULT_MAG_SIZE!s}"
        f"&width={DEFAULT_WIDTH / DEFAULT_MAG_SIZE!s}"
        f"&maxwidth={DEFAULT_WIDTH!s}"
        f"&plotwidth={DEFAULT_WIDTH!s}"
        f"&location={DEFAULT_SEMATIC_LOCATION}"
        f"&longlat={DEFAULT_LONGLAT}"
        f"&ip={DEFAULT_IP_ADDR}"
    )

    # Get the query response
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(query_url) as r:
                if r.status == 200:
                    # Read the response, interp as json, and return
                    data = await r.read()
                    return json.loads(data.decode("utf8"))
                return None
        except Exception as e:
            raise WolframAPIError("Unable to establish connection with Wolfram Alpha's API at `get_query`", e) from None


async def _report_api_error(ctx: Context, e: WolframAPIError) -> None:
    """
    Log a WolframAPIError and report it to the user via the shared traceback layout.
    """
    ctx.log(
        f"Failed to get data from Wolfram Alpha API: {e}\nError message: {e.err_msg}",
        level=logging.ERROR,
    )
    await ctx.traceback(APIErrorDesc, f"{e}:\n{e.err_msg}")


MAX_ENTRIES_PER_PAGE = 5
RESULTS_HEADER = "Results from Wolfram Alpha Pro"
TEASER_POD_COUNT = 2


def _build_page(entries: list[tuple[str, str, int]], text: bool, footer_text: str, colour: discord.Colour) -> Container:
    container = Container(Header(RESULTS_HEADER, 3), Separator(), accent_colour=colour)
    for title, content, _ in entries:
        container.add_item(Body(bf(discord.utils.escape_mentions(title))))
        if text:
            container.add_item(Body(discord.utils.escape_mentions(content)))
        else:
            container.add_item(MediaGallery(discord.MediaGalleryItem(content)))
    container.add_item(Footer(footer_text))
    return container


def build_pages(pods: list[dict], text: bool, footer_text: str, colour: discord.Colour) -> tuple[list[Container], int]:
    """
    Flattens every pod into (title, content, pod_index) entries.


    Returns the built pages, and the index of the teaser page (always 0).
    """
    teaser: list[tuple[str, str, int]] = []
    rest: list[tuple[str, str, int]] = []
    for i, pod in enumerate(pods):
        is_teaser_pod = i < TEASER_POD_COUNT
        for sub in (pod, *pod.get("subpods", [])):
            content = sub.get("plaintext") if text else sub.get("img", {}).get("src")
            if content:
                title = sub.get("title") or pod["title"]
                (teaser if is_teaser_pod else rest).append((title, content, i))

    chunks = [rest[i : i + MAX_ENTRIES_PER_PAGE] for i in range(0, len(rest), MAX_ENTRIES_PER_PAGE)]
    if teaser:
        chunks.insert(0, teaser)

    pages = [_build_page(chunk, text, footer_text, colour) for chunk in chunks]
    return pages, 0


@module.cmd(
    "query",
    desc=f"Query the [Wolfram Alpha computation engine]({WEB}).",
    flags=["text", "t"],
    aliases=["ask", "wolf", "wa", "?w"],
)
async def cmd_query(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}ask [query] [--text/-t]
    Description:
        Sends the query to the Wolfram Alpha computational engine and returns the result.
        The reply opens on the top result; press the button to browse the rest.
    Flags::
        text, t: Respond with copyable text instead of images, where possible.
    """
    # Hack to disallow `w` being used with no space
    if ctx.alias == "w":
        true_args = ctx.msg.content.strip()[len(ctx.prefix) :].strip()[1:]
        if not true_args or true_args[0] not in (" ", "\n"):
            return None

    prefix = await ctx.best_prefix()
    text = flags["text"] or flags["t"]

    # Handle no arguments
    if not ctx.args:
        return await ctx.error_reply(
            f"Please submit a valid query! For example, `{prefix}ask differentiate x+y^2 with respect to x`.",
        )

    appid = ctx.get_guild_setting.wolfram_id.value if ctx.guild else None
    if appid:
        custom_appid = True
    else:
        custom_appid = False
        appid = ctx.client.conf.get("wolfram_id").strip()

    # Query the API, handle errors
    t_start = time.monotonic()
    async with ctx.ch.typing():
        try:
            result = await get_query(ctx.args, appid)
        except WolframAPIError as e:
            return await _report_api_error(ctx, e)
        except Exception:
            try:
                result = await get_query(ctx.args, ctx.client.conf.get("WOLFRAM_ID").strip())
            except WolframAPIError as e:
                return await _report_api_error(ctx, e)
            except Exception:
                return await ctx.error_reply(
                    "An unknown exception occurred while fetching the Wolfram Alpha query!\n"
                    "If the problem persists please contact support.",
                )
    t_query = time.monotonic()
    ctx.log(f"Wolfram Alpha responded in {t_query - t_start:.2f}s.", level=logging.DEBUG)

    if not result:
        return await ctx.error_reply(
            "Failed to get a response from Wolfram Alpha.\nIf the problem persists, please contact support.",
        )
    if "queryresult" not in result:
        return await ctx.error_reply(
            "Did not get a valid response from Wolfram Alpha.\nIf the problem persists, please contact support.",
        )

    queryresult = result["queryresult"]
    if not queryresult["success"] or queryresult["numpods"] == 0:
        if queryresult["error"] and "code" in queryresult["error"]:
            error = queryresult["error"]
            if custom_appid:
                if error["code"] == "1":
                    desc = (
                        "Couldn't send your query!\n"
                        "**Error:** Invalid Wolfram Alpha `AppID`!\n"
                        "Please ask a guild admin to re-configure the `wolfram_id`.\n"
                        f"(See `{prefix}config wofram_id` for more information.)"
                    )
                else:
                    desc = ("An unknown error occurred querying the WolframAlpha API!\n**ERROR:** {}\t{}").format(
                        error["code"],
                        error["msg"],
                    )
            else:
                desc = (
                    "There was an unhandled error querying the WolframAlpha API!\n"
                    "This should be fixed soon, but if the issue persists, please contact "
                    "[our support team]({})."
                ).format(ctx.client.app_info["support_guild"])
        else:
            desc = "Wolfram Alpha doesn't understand your query!\nPerhaps try rephrasing your question?"
        return await ctx.error_reply(desc)

    pods = queryresult["pods"]
    footer_text = f"Requested by {ctx.author}"
    pages, start_page = build_pages(pods, text, footer_text, discord.Colour.from_str("#DD1100"))
    t_built = time.monotonic()
    ctx.log(f"Built {len(pages)} page(s) in {t_built - t_query:.2f}s.", level=logging.DEBUG)

    if not pages:
        return await ctx.error_reply(
            "This result doesn't have any copyable text to show.\nTry again without `--text`/`-t` to see it as images."
            if text
            else "This result doesn't have any content to show.",
        )

    more_emoji = ctx.client.conf.emojis.getemoji("more", MORE_EMOJI)
    message = await ctx.pager_v2_pages(
        pages,
        view_cls=TeaserPagerView,
        view_kwargs={"start_page": start_page, "more_emoji": more_emoji},
    )
    t_sent = time.monotonic()
    ctx.log(
        f"Sent reply in {t_sent - t_built:.2f}s (total {t_sent - t_start:.2f}s).",
        level=logging.DEBUG,
    )
    return message
