"""
Wolfram Alpha command implementation.
"""

import asyncio
import json
import logging
import time
from io import BytesIO
from urllib import parse

import aiohttp
import discord
from cmdClient import Context  # noqa
from cmdClient.Format import bf, hyperlink
from cmdClient.Layouts import Body, Footer, Header
from discord import Colour, File, MediaGalleryItem
from discord.ui import Container, MediaGallery, Separator

from . import wolf_data
from .module import maths_module as module
from .wolf_layouts import MORE_EMOJI, TeaserPagerView

ENDPOINT = "http://api.wolframalpha.com/v2/query?"
SHORT_ENDPOINT = "http://api.wolframalpha.com/v1/result?"
WOLFRAM_WEB = "https://www.wolframalpha.com/"

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


async def get_short_answer(query: str, appid: str) -> tuple[int, str]:
    """
    Fetches the provided query from Wolfram Alpha's Short Answers API.

    Arguments:
        query: The query to post.
        appid: The Wolfram Appid to use in the query.
    Returns:
        A tuple of (http status, response body text). The body is only meaningful when the status is 200.
    """
    query_url: str = (
        f"{SHORT_ENDPOINT}appid={appid}&i={parse.quote_plus(query)}"
        "&units=metric"
        f"&location={DEFAULT_SEMATIC_LOCATION}"
        f"&longlat={DEFAULT_LONGLAT}"
        f"&ip={DEFAULT_IP_ADDR}"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(query_url) as r:
                return r.status, await r.text()
        except Exception as e:
            raise WolframAPIError(
                "Unable to establish connection with Wolfram Alpha's API at `get_short_answer`", e
            ) from None


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
MAX_ATTACHED_IMAGES = 10


async def _fetch_image_file(session: aiohttp.ClientSession, url: str, filename: str) -> File | None:
    """
    Downloads `url` and wraps it as a `File` so it can be re-hosted as a Discord attachment, since Wolfram's own image URLs expire and eventually show as broken.
    Returns None on any failure, so the caller can fall back to the original URL.
    """
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
    except Exception:
        return None
    return File(BytesIO(data), filename=filename)


def _build_page(
    entries: list[tuple[str, str, int]],
    footer_text: str,
    colour: Colour,
    files_by_url: dict[str, File],
) -> Container:
    container = Container(Header(RESULTS_HEADER, 3), Separator(), accent_colour=colour)
    for title, content, _ in entries:
        container.add_item(Body(bf(discord.utils.escape_mentions(title))))
        media = files_by_url.get(content, content)
        container.add_item(MediaGallery(MediaGalleryItem(media)))
    container.add_item(Footer(footer_text))
    return container


async def build_pages(
    pods: list[dict],
    footer_text: str,
    colour: Colour,
) -> tuple[list[Container], int, list[File]]:
    """
    Flattens every pod into (title, content, pod_index) entries.

    Downloads and re-attaches as many of the pod images as fit within
    `MAX_ATTACHED_IMAGES`; any beyond that budget keep Wolfram's original URL.

    Returns the built pages, the index of the teaser page (always 0), and the
    list of downloaded attachments to send alongside the pages.
    """
    teaser: list[tuple[str, str, int]] = []
    rest: list[tuple[str, str, int]] = []
    for i, pod in enumerate(pods):
        is_teaser_pod = i < TEASER_POD_COUNT
        for sub in (pod, *pod.get("subpods", [])):
            content = sub.get("img", {}).get("src")
            if content:
                title = sub.get("title") or pod["title"]
                (teaser if is_teaser_pod else rest).append((title, content, i))

    chunks = [rest[i : i + MAX_ENTRIES_PER_PAGE] for i in range(0, len(rest), MAX_ENTRIES_PER_PAGE)]
    if teaser:
        chunks.insert(0, teaser)

    urls = list(dict.fromkeys(url for chunk in chunks for _, url, _ in chunk))[:MAX_ATTACHED_IMAGES]
    files_by_url: dict[str, File] = {}
    attachments: list[File] = []
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *(_fetch_image_file(session, url, f"wolf_{i}.png") for i, url in enumerate(urls)),
        )
    for url, file in zip(urls, results, strict=True):
        if file is not None:
            files_by_url[url] = file
            attachments.append(file)

    pages = [_build_page(chunk, footer_text, colour, files_by_url) for chunk in chunks]
    return pages, 0, attachments


async def _reply_short_answer(ctx: Context, appid: str, custom_appid: bool, prefix: str):
    """
    Fetches and replies with a plain-text answer from Wolfram Alpha's Short Answers API.
    """
    t_start = time.monotonic()
    async with ctx.ch.typing():
        try:
            status, answer = await get_short_answer(ctx.args, appid)
        except WolframAPIError as e:
            return await _report_api_error(ctx, e)
        except Exception:
            try:
                status, answer = await get_short_answer(
                    ctx.args, ctx.client.conf.get("WOLFRAM_API_SHORTANSWERS").strip()
                )
            except WolframAPIError as e:
                return await _report_api_error(ctx, e)
            except Exception:
                return await ctx.error_reply(
                    "An unknown exception occurred while fetching the Wolfram Alpha query!\n"
                    "If the problem persists please contact support.",
                )
    t_query = time.monotonic()
    ctx.log(f"Wolfram Alpha responded in {t_query - t_start:.3f}s.", level=logging.DEBUG)

    if status == 403:
        if custom_appid:
            desc = (
                "Couldn't send your query!\n"
                "**Error:** Invalid Wolfram Alpha `AppID`!\n"
                "Please ask a guild admin to re-configure the `wolfram_short_id`.\n"
                f"(See `{prefix}config wolfram_short_id` for more information.)"
            )
        else:
            desc = (
                "There was an unhandled error querying the WolframAlpha API!\n"
                "This should be fixed soon, but if the issue persists, please contact "
                "[our support team]({})."
            ).format(ctx.client.app_info["support_guild"])
        return await ctx.error_reply(desc)
    if status != 200 or not answer.strip():
        return await ctx.error_reply(
            "Wolfram Alpha doesn't have a short answer for your query.\n"
            f"Try `{prefix}wa {ctx.args} --full` for the full result, or rephrase your question.",
        )

    message = await ctx.reply(
        f"```\n{discord.utils.escape_mentions(answer.replace('  ', ' ').strip())}\n```",
        reference=ctx.msg.to_reference(),
        allowed_mentions=discord.AllowedMentions.none(),
    )
    t_sent = time.monotonic()
    ctx.log(
        f"Sent reply in {t_sent - t_query:.3f}s (total {t_sent - t_start:.3f}s).",
        level=logging.DEBUG,
    )
    return message


@module.cmd(
    "wolframalpha",
    desc=f"Query the [Wolfram Alpha computation engine]({WOLFRAM_WEB}).",
    flags=["full", "f"],
    aliases=["wa"],
)
async def cmd_query(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}wa [query] [--full/-f]
    Description:
        Sends the query to the Wolfram Alpha computational engine and returns the result.
        By default this returns a quick short answer; pass `--full` for the full,
        multi-pod result with images.
        The reply opens on the top result; press the button to browse the rest.
    Flags::
        full, f: Fetch the full, multi-pod result instead of the short answer.
    """
    # Hack to disallow `w` being used with no space
    if ctx.alias == "w":
        true_args = ctx.msg.content.strip()[len(ctx.prefix) :].strip()[1:]
        if not true_args or true_args[0] not in (" ", "\n"):
            return None

    prefix = await ctx.best_prefix()
    full = flags["full"] or flags["f"]

    # Handle no arguments
    if not ctx.args:
        return await ctx.error_reply(
            f"Please submit a valid query! For example, `{prefix}wa differentiate x+y^2 with respect to x`.",
        )

    if ctx.guild:
        appid = ctx.get_guild_setting.wolfram_id.value if full else ctx.get_guild_setting.wolfram_short_id.value
    else:
        appid = None
    if appid:
        custom_appid = True
    else:
        custom_appid = False
        appid = ctx.client.conf.get("WOLFRAM_API_FULLRESULT" if full else "WOLFRAM_API_SHORTANSWERS").strip()

    if not full:
        return await _reply_short_answer(ctx, appid, custom_appid, prefix)

    # Query the API, handle errors
    t_start = time.monotonic()
    async with ctx.ch.typing():
        try:
            result = await get_query(ctx.args, appid)
        except WolframAPIError as e:
            return await _report_api_error(ctx, e)
        except Exception:
            try:
                result = await get_query(ctx.args, ctx.client.conf.get("WOLFRAM_API_FULLRESULT").strip())
            except WolframAPIError as e:
                return await _report_api_error(ctx, e)
            except Exception:
                return await ctx.error_reply(
                    "An unknown exception occurred while fetching the Wolfram Alpha query!\n"
                    "If the problem persists please contact support.",
                )
    t_query = time.monotonic()
    ctx.log(f"Wolfram Alpha responded in {t_query - t_start:.3f}s.", level=logging.DEBUG)

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
                        f"(See `{prefix}config wolfram_id` for more information.)"
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
    footer_text = f"Requested by {ctx.author} | {hyperlink('View on Wolfram Alpha', f'{WOLFRAM_WEB}input/?i={parse.quote_plus(ctx.args, safe='')}')}"
    pages, start_page, attachments = await build_pages(pods, footer_text, Colour.from_str("#DD1100"))
    t_built = time.monotonic()
    ctx.log(f"Built {len(pages)} page(s) in {t_built - t_query:.3f}s.", level=logging.DEBUG)

    if not pages:
        return await ctx.error_reply("This result doesn't have any content to show.")

    more_emoji = ctx.client.conf.emojis.getemoji("more", MORE_EMOJI)
    message = await ctx.pager_v2_pages(
        pages,
        view_cls=TeaserPagerView,
        view_kwargs={"start_page": start_page, "more_emoji": more_emoji},
        files=attachments,
    )
    t_sent = time.monotonic()
    ctx.log(
        f"Sent reply in {t_sent - t_built:.3f}s (total {t_sent - t_start:.3f}s).",
        level=logging.DEBUG,
    )
    return message
