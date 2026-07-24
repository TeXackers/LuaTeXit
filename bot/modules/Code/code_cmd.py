import asyncio
import shutil
from contextlib import suppress

import anyio.to_thread
import discord
from anyio import Path as AsyncPath
from cmdClient import Context  # noqa
from utils.ratelimit import Bucket, BucketFull, BucketOverFull
from wards import is_admin

from modules.Tex.core.LatexContext import LatexContext

from .core.CodeLayouts import CodeOutputView, build_code_pages
from .module import code_module as module
from .resources import staging_root

# Recognised codeblock language tags, mapped to their canonical Discord highlighting syntax.
_LANG_ALIASES: dict[str, str] = {
    "python": "python",
    "py": "python",
    "r": "r",
}

# Per-user ratelimiting, mirrors the Typst compile pipeline (`TypstContext.make`).
_user_buckets: dict[int, Bucket] = {}
_user_locks: dict[int, asyncio.Lock] = {}
MAX_IMAGES = 10


async def _cleanup_staging(targetid: str) -> None:
    """
    Remove the target's staging directory in the background once any output (like a PNG) has already been read and uploaded, to reclaim tmpfs.
    """
    with suppress(asyncio.CancelledError):
        await anyio.to_thread.run_sync(shutil.rmtree, f"{staging_root}/{targetid}", True)


@module.cmd(
    "code",
    desc="Runs Python or R code and displays it, with any plot output.",
)
@is_admin()
async def cmd_code(ctx: Context):
    """
    Usage``:
        {prefix}code <codeblock>
    Description:
        Runs the given Python or R code in a sandboxed subprocess and replies with the result: any plot it produced, its printed output, and the syntax-highlighted source.

        Your code must be in a `python`/`py` or `r` codeblock, see the example below.

        *Restricted to bot administrators.*
    Examples``:
        {prefix}code
    """
    no_codeblock_msg = (
        "Please give me some code in a codeblock, for example "
        "```\n"
        f"{await ctx.best_prefix()}code\n"
        "\\`\\`\\`python\n"
        "print('hello world')\n"
        "\\`\\`\\`\n"
        "```\n"
        "-# Only python and R are supported at this stage."
    )
    if not ctx.args:
        return await ctx.error_reply(no_codeblock_msg)

    content = ctx.clean_arg_str()
    codeblocks = LatexContext.extract_codeblocks(content)
    match = next(
        ((_LANG_ALIASES[tag.lower()], code) for tag, code in codeblocks if tag and tag.lower() in _LANG_ALIASES),
        None,
    )
    if match is None:
        return await ctx.error_reply(no_codeblock_msg)

    lang, source = match
    userid = ctx.author.id

    # Retrieve and request the user's bucket, creating it if required
    if userid not in _user_buckets:
        _user_buckets[userid] = Bucket(3, 30)

    try:
        _user_buckets[userid].request()
    except BucketOverFull:
        # A warning was already given, fail silently
        return None
    except BucketFull:
        return await ctx.error_reply("Too many requests, please slow down!\n(You may try again in a moment.)")

    # Retrieve the user lock, creating it if required
    if userid not in _user_locks:
        _user_locks[userid] = asyncio.Lock()

    async with _user_locks[userid]:
        # Don't run if the bucket became overfull while we were waiting on the lock
        if _user_buckets[userid].overfull:
            return None

        targetid = str(userid)
        async with ctx.ch.typing():
            output, success = await ctx.run_code(source, lang, targetid)

        image_paths: list[AsyncPath] = []
        if success:
            image_dir = AsyncPath(f"{staging_root}/{targetid}")
            image_paths = sorted(
                [p async for p in image_dir.glob(f"{targetid}_*.png")],
                key=lambda p: p.name,
            )[:MAX_IMAGES]
        image_filenames = [p.name for p in image_paths]
        failed = not success

        pages = build_code_pages(source, lang, output, failed, image_filenames, shown=False)
        files = [discord.File(p, filename=p.name) for p in image_paths] or None

        await ctx.pager_v2_pages(
            pages,
            view_cls=CodeOutputView,
            view_kwargs={
                "source": source,
                "syntax": lang,
                "output": output,
                "failed": failed,
                "image_filenames": image_filenames,
            },
            files=files,
        )

        cleanup_task = asyncio.ensure_future(_cleanup_staging(targetid))
        ctx.tasks.append(cleanup_task)

    return None
