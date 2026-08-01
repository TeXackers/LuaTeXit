import asyncio
from collections.abc import Callable, Iterable, Sequence
from contextlib import suppress

import discord
from cmdClient import Context
from cmdClient.Interaction import PagerView
from cmdClient.Layouts import Body, Header
from cmdClient.lib import ResponseTimedOut, UserCancelled
from constants import LuaTeXitCC
from discord import Emoji
from discord.ui import Container, Separator

from .cache import async_ttl_cache
from .lib import paginate_list, split_text


@async_ttl_cache(days=30)
async def _fetch_application_emojis(client) -> list[Emoji]:
    """Fetch (and cache) the raw list of the bot application's custom emojis."""
    return await client.fetch_application_emojis()


async def get_application_emoji_by_id(client, emoji_id: int) -> Emoji:
    """
    Look up one of the bot application's custom emojis by id.

    Application emojis essentially never change, so this goes through a long-lived
    cache instead of hitting the Discord API on every single use.
    """
    emojis: list[Emoji] = await _fetch_application_emojis(client)
    emoji: Emoji | None = next((e for e in emojis if e.id == emoji_id), None)
    if emoji is None:
        raise LookupError(f"No application emoji found with id={emoji_id}.")
    return emoji


async def get_application_emoji_by_name(client, name: str) -> Emoji:
    """
    Look up one of the bot application's custom emojis by name. See `get_application_emoji_by_id`.
    """
    emojis: list[Emoji] = await _fetch_application_emojis(client)
    emoji: Emoji | None = next((e for e in emojis if e.name == name), None)
    if emoji is None:
        raise LookupError(f"No application emoji found with name={name!r}.")
    return emoji


async def get_application_emojis_by_name(client) -> dict[str, Emoji]:
    """
    Fetch and cache _all_ of the bot application's custom emojis, key'e'd by name. Useful for looking up multiple emojis by name.
    """
    emojis: list[Emoji] = await _fetch_application_emojis(client)
    return {e.name: e for e in emojis}


@Context.util
async def listen_for(
    ctx: Context,
    allowed_input: list | None = None,
    timeout: int = 120,
    lower: bool = True,
    check_fn: Callable[[discord.Message], bool] | None = None,
):
    """
    Listen for a one of a particular set of input strings,
    sent in the current channel by `ctx.author`.
    When found, return the message containing them.

    Parameters
    ----------
    allowed_input: Union(List(str), None)
        List of strings to listen for.
        Allowed to be `None` precisely when a `check_fn` function is also supplied.
    timeout: int
        Number of seconds to wait before timing out.
    lower: bool
        Whether to shift the allowed and message strings to lowercase before checking.
    check_fn: Function(message) -> bool
        Alternative custom check function.

    Returns: discord.Message
        The message that was matched.

    Raises
    ------
    cmdClient.lib.ResponseTimedOut:
        Raised when no messages matching the given criteria are detected in `timeout` seconds.
    """
    # Generate the check if it hasn't been provided
    if not check_fn:
        # Quick check the arguments are sane
        if not allowed_input:
            raise ValueError("allowed_input and check_fn cannot both be None")

        # Force a lower on the allowed inputs
        allowed_input = [s.lower() for s in allowed_input]

        # Create the check function
        def _default_check(message: discord.Message) -> bool:
            result = message.author == ctx.author
            result = result and (message.channel == ctx.ch)
            return result and ((message.content.lower() if lower else message.content) in allowed_input)

        check_fn = _default_check

    # Wait for a matching message, catch and transform the timeout
    try:
        message = await ctx.client.wait_for("message", check=check_fn, timeout=timeout)
    except asyncio.TimeoutError:
        raise ResponseTimedOut("Session timed out waiting for user response.") from None

    return message


@Context.util
async def selector(
    ctx: Context, header: str, select_from: list[str], timeout: int = 120, max_len: int = 20, allow_single: bool = True
):
    """
    Interactive routine to prompt the `ctx.author` to select an item from a list.
    Returns the list index that was selected.

    Parameters
    ----------
    header: str
        String to put at the top of each page of selection options.
        Intended to be information about the list the user is selecting from.
    select_from: list[str]
        The list of strings to select from.
    timeout: int
        The number of seconds to wait before throwing `ResponseTimedOut`.
    max_len: int
        The maximum number of items to display on each page.
        Decrease this if the items are long, to avoid going over the char limit.
    allow_single: bool
        Whether to show the selector for only one option.

    Returns
    -------
    int:
        The index of the list entry selected by the user.

    Raises
    ------
    cmdClient.lib.UserCancelled:
        Raised if the user manually cancels the selection.
    cmdClient.lib.ResponseTimedOut:
        Raised if the user fails to respond to the selector within `timeout` seconds.
    """
    # Handle improper arguments
    if len(select_from) == 0:
        raise ValueError("Selection list passed to `selector` cannot be empty.")

    # Handle having a single item to select
    if len(select_from) == 1 and not allow_single:
        return 0

    # Generate the selector pages
    footer = "Please type the number corresponding to your selection, or type `c` now to cancel."
    list_pages: list[str] = paginate_list(select_from, block_length=max_len)
    pages: list[str] = [f"{header}\n{page}\n{footer}" for page in list_pages]

    # Post the pages in a paged message
    out_msg = await ctx.pager(pages)

    # Listen for valid input
    valid_input = [str(i + 1) for i in range(len(select_from))] + ["c", "C"]
    try:
        result_msg = await ctx.listen_for(valid_input, timeout=timeout)
    except ResponseTimedOut:
        raise ResponseTimedOut("Selector timed out waiting for a response.") from None

    # Try and delete the selector message and the user response.
    with suppress(discord.NotFound, discord.Forbidden):
        await out_msg.delete()
        await result_msg.delete()

    # Handle user cancellation
    if result_msg.content in ["c", "C"]:
        raise UserCancelled("User cancelled selection.")

    # The content must now be a valid index. Collect and return it.
    return int(result_msg.content) - 1


@Context.util
async def multi_selector(
    ctx: Context, header: str, select_from: list[str], timeout: int = 120, max_len: int = 20, allow_single: bool = True
):
    """
    Interactive routine to prompt the `ctx.author` to select multiple items from a list.
    Returns a list of list indices that were selected.

    Parameters
    ----------
    header: str
        String to put at the top of each page of selection options.
        Intended to be information about the list the user is selecting from.
    select_from: list[str]
        The list of strings to select from.
    timeout: int
        The number of seconds to wait before throwing `ResponseTimedOut`.
    max_len: int
        The maximum number of items to display on each page.
        Decrease this if the items are long, to avoid going over the char limit.
    allow_single: bool
        Whether to show the selector for only one option.

    Returns
    -------
    list[int]:
        The list of indices selected by the user.

    Raises
    ------
    cmdClient.lib.UserCancelled:
        Raised if the user manually cancels the selection.
    cmdClient.lib.ResponseTimedOut:
        Raised if the user fails to respond to the selector within `timeout` seconds.
    """
    # Handle improper arguments
    if len(select_from) == 0:
        raise ValueError("Selection list passed to `selector` cannot be empty.")

    # Handle having a single item to select
    if len(select_from) == 1 and not allow_single:
        return [0]

    # Generate the selector pages
    footer = (
        "Please type the numbers corresponding to your selection, "
        "separated by commas, or type `c` now to cancel. (E.g. `2, 3, 5, 7, 11`)"
    )
    list_pages = paginate_list(select_from, block_length=max_len)
    pages = [f"{header}\n{page}\n{footer}" for page in list_pages]

    # Post the pages in a paged message
    out_msg = await ctx.pager(pages)

    # Listen for valid input
    valid_num_strs: set = {str(i + 1) for i in range(len(select_from))}

    def _check(message):
        if not ((message.channel == ctx.ch) and (message.author == ctx.author)):
            return False
        if not message.content:
            return False

        content = message.content.lower()
        return (content == "c") or all(chars.strip() in valid_num_strs for chars in content.split(","))

    try:
        result_msg = await ctx.client.wait_for("message", check=_check, timeout=timeout)
    except asyncio.TimeoutError:
        raise ResponseTimedOut("Selector timed out waiting for a response.") from None

    # Try and delete the selector message and the user response.
    with suppress(discord.NotFound, discord.Forbidden):
        await out_msg.delete()
        await result_msg.delete()

    # Handle user cancellation
    if result_msg.content in ["c", "C"]:
        raise UserCancelled("User cancelled selection.")

    # The content must now be a valid set of indices. Collect and return it.
    return [int(chars.strip()) - 1 for chars in result_msg.content.split(",")]


@Context.util
async def pager_v2_pages(
    ctx: Context,
    pages: Iterable[Container],
    view_cls: type[PagerView] = PagerView,
    view_kwargs: dict | None = None,
    files: Sequence[discord.File] | None = None,
):
    """
    Reply to `ctx` with a pre-built sequence of `Container` pages,
    browsable with buttons via a `cmdClient.Interaction.PagerView`.

    This is the Components V2 counterpart of `ctx.pager`, for callers
    (e.g. `tex_pagination_v2`) that build their own pages instead of
    relying on `ctx.pager_v2` to split raw text.

    Parameters
    ----------
    ctx: Context
        The context to reply to.
    pages: Iterable[Container]
        The pre-built pages to browse.
    view_cls: type[PagerView]
        The `PagerView` subclass to render, for callers that need extra buttons/behaviour.
    view_kwargs: dict | None
        Extra keyword arguments to pass through to `view_cls`.
    files: Sequence[discord.File] | None
        Attachments referenced (via `attachment://<filename>`) by any of the pages,
        e.g. images the caller downloaded so they persist as Discord attachments
        instead of hotlinking an external URL. Uploaded once with the initial reply,
        and stay available to every page since later/earlier page switches only swap
        the view rather than re-sending attachments.
    Returns: discord.Message
        The message the pager was sent in.
    """
    # get emojis
    left_emoji = await get_application_emoji_by_name(ctx.client, "left")
    right_emoji = await get_application_emoji_by_name(ctx.client, "right")

    view = view_cls(
        list(pages),
        locked=True,
        author=ctx.author,
        left_emoji=left_emoji,
        right_emoji=right_emoji,
        **(view_kwargs or {}),
    )
    message = await ctx.reply(view=view, files=list(files) if files else None)
    view.message = message
    return message


@Context.util
async def pager_v2(
    ctx: Context,
    content: str | Iterable,
    title: str | None = None,
    block_length: int = 1000,
    code: bool = False,
    colour: str | discord.Colour = LuaTeXitCC["yellow"],
    view_cls: type[PagerView] = PagerView,
    view_kwargs: dict | None = None,
    **kwargs,
):
    """
    Reply to `ctx` with `content` split into pages of at most `block_length` characters,
    browsable with buttons via a `cmdClient.Interaction.PagerView`.

    Parameters
    ----------
    ctx: Context
        The context to reply to.
    content: str
        The long text content to browse.
    title: str | None
        Optional heading shown on every page.
    block_length: int
        Maximum number of characters per page.
    code: bool
        Whether to wrap each page in codeblocks.
    colour: str | None
        The colour of the LayoutView, if applicable.
    view_cls: type[PagerView]
        The `PagerView` subclass to render, for callers that need extra buttons/behaviour.
    view_kwargs: dict | None
        Extra keyword arguments to pass through to `view_cls`.
    Returns: discord.Message
        The message the pager was sent in.
    """
    blocks = split_text(
        content,
        blocksize=block_length,
        code=code,
        **kwargs,
    )
    pages = [
        Container(
            *([Header(title)] if title else []),
            Separator(),
            Body(block),
            accent_colour=colour if isinstance(colour, discord.Colour) else discord.Colour.from_str(colour),
        )
        for block in blocks
    ]

    return await ctx.pager_v2_pages(pages, view_cls=view_cls, view_kwargs=view_kwargs)


@Context.util
async def pager(
    ctx: Context,
    pages: Sequence[str | discord.Embed],
    locked: bool = True,
    blocking: bool = False,
    destination: discord.abc.Messageable | None = None,
    start_page=0,
    **kwargs,
) -> discord.Message:
    """
    Shows the user each page from the provided list `pages` one at a time,
    providing reactions to page back and forth between pages.
    This is done asynchronously, and returns after displaying the first page.

    Parameters
    ----------
    pages: Sequence[str | discord.Embed]
        A list of either strings or embeds to display as the pages.
    locked: bool
        Whether only the `ctx.author` should be able to use the paging reactions.
    blocking: bool
        Whether to block until the pager has finished.
        Useful for cancelling tasks when the pager completes.
    destination: discord.Messageable | None
        Optional custom destination to use instead of `ctx.ch`.
    start_page: int | None
        Optional initial page to display.
    kwargs: ...
        Remaining keyword arguments are transparently passed to the sender method.

    Returns: discord.Message
        This is the output message, returned for easy deletion.
    """
    # Handle broken input
    if len(pages) == 0:
        raise ValueError("Pager cannot page with no pages!")

    # Identify sender method based on destination
    sender = ctx.reply if destination is None or destination == ctx.ch else destination.send

    # Post first page. Method depends on whether the page is an embed or not.
    first_page = pages[start_page]
    if isinstance(first_page, discord.Embed):
        out_msg = await sender(embed=first_page, **kwargs)
    else:
        out_msg = await sender(first_page, **kwargs)

    # Run the paging loop if required
    if len(pages) > 1:
        task = asyncio.ensure_future(_pager(ctx, out_msg, pages, locked, start_page=start_page))
        if blocking:
            await task

    # Return the output message
    return out_msg


async def _pager(ctx, out_msg, pages, locked, start_page=0):
    """
    Asynchronous initialiser and loop for the `pager` utility above.
    """
    # Page number
    page = start_page

    # Add reactions to the output message
    next_emoji = ctx.client.conf.emojis.getemoji("next", "▶")
    prev_emoji = ctx.client.conf.emojis.getemoji("prev", "◀")

    try:
        await out_msg.add_reaction(prev_emoji)
        await out_msg.add_reaction(next_emoji)
    except discord.Forbidden:
        # We don't have permission to add paging emojis
        # Die as gracefully as we can
        await ctx.error_reply("Cannot page results because I do not have permissions to react!")
        return

    # Check function to determine whether a reaction is valid
    def check(reaction, user):
        result = reaction.message.id == out_msg.id
        result = result and reaction.emoji in [next_emoji, prev_emoji]
        result = result and (user.id != ctx.client.user.id)

        return result and not (locked and user != ctx.author)

    # Begin loop
    while True:
        # Wait for a valid reaction, break if we time out
        try:
            reaction, user = await ctx.client.wait_for("reaction_add", check=check, timeout=300)
        except asyncio.TimeoutError, asyncio.CancelledError:
            break

        # Attempt to remove the user's reaction, silently ignore errors
        task = asyncio.ensure_future(_safe_async_future(out_msg.remove_reaction(reaction.emoji, user)))
        task.add_done_callback(lambda t: ctx.client.background_tasks.discard(t))

        # Change the page number
        page += 1 if reaction.emoji == next_emoji else -1
        page %= len(pages)

        # Edit the message with the new page
        active_page = pages[page]
        if isinstance(active_page, discord.Embed):
            await out_msg.edit(embed=active_page)
        else:
            await out_msg.edit(content=active_page)

    # Clean up by removing the reactions
    try:
        await out_msg.clear_reactions()
    except discord.Forbidden:
        try:
            await out_msg.remove_reaction(next_emoji, ctx.client.user)
            await out_msg.remove_reaction(prev_emoji, ctx.client.user)
        except discord.NotFound:
            pass
    except discord.NotFound:
        pass


async def _safe_async_future(future):
    """
    Waits for the given future and ignores any errors that arise.
    Use inside `asyncio.ensure_future` to silence errors.
    """
    with suppress(Exception):
        await future


@Context.util
async def on_input(
    ctx: Context, msg: str | discord.Message | None = None, delete_after: bool = True, timeout: int = 120
):
    """
    Listen for a response in the current channel, from ctx.author.
    Returns the response from ctx.author, if it is provided.
    Parameters
    ----------
    msg: str | discord.Message | None
        When given a `Message`, treats it as the prompt message.
        When given a string, sends the message and uses it as the prompt message.
        Will use a default message if not provided.
    delete_after: bool
        Whether to delete the prompt message after input is given.
    timeout: int
        Number of seconds to wait before timing out.
    Raises
    ------
    cmdClient.lib.ResponseTimedOut:
        Raised when ctx.author does not provide a response before the function times out.
    """
    # Deliver prompt
    if msg is None or isinstance(msg, str):
        offer_msg = await ctx.reply(msg or "Please enter your input.")
    elif isinstance(msg, discord.Message):
        offer_msg = msg
    else:
        raise ValueError("Invalid prompt message given.")

    # Criteria for the input message
    def checks(m):
        return m.author == ctx.author and m.channel == ctx.ch

    # Listen for the reply
    try:
        result_msg = await ctx.client.wait_for("message", check=checks, timeout=timeout)
    except asyncio.TimeoutError:
        raise ResponseTimedOut("Session timed out waiting for user response.") from None

    result = result_msg.content

    # Attempt to delete the prompt and reply messages
    if delete_after:
        with suppress(Exception):
            await offer_msg.delete()
            await result_msg.delete()

    return result


@Context.util
async def ask(ctx, msg, timeout=30, use_msg=None, add_hints=True, del_on_timeout=False):
    """
    Ask ctx.author a yes/no question.
    Returns 0 if ctx.author answers no
    Returns 1 if ctx.author answers yes
    Parameters
    ----------
    msg: string
        Adds the question to the message string.
        Requires an input.
    timeout: int
        Number of seconds to wait before timing out.
    use_msg: discord.Message
        Edit a pre-sent message with the prompt, instead of sending a new message.
    add_hints: bool
        Whether to add the answer hints to the prompt.
    del_on_timeout: bool
        Whether to delete the question if it times out.
    Raises
    ------
    Nothing
    """
    out = "{} {}".format(msg, "`y(es)`/`n(o)`") if add_hints else msg

    offer_msg = use_msg or await ctx.reply(out)
    if use_msg:
        await use_msg.edit(content=msg)

    result_msg = await ctx.listen_for(["y", "yes", "n", "no"], timeout=timeout)

    if result_msg is None:
        if del_on_timeout:
            with suppress(Exception):
                await offer_msg.delete()
        return None
    result = result_msg.content.lower()
    with suppress(Exception):
        if not use_msg:
            await offer_msg.delete()
        await result_msg.delete()

    if result in ["n", "no"]:
        return 0
    return 1
