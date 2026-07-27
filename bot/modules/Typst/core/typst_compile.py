import functools
import logging
import shutil
from pathlib import Path

import anyio.to_thread
from anyio import Path as AsyncPath
from cmdClient import Context
from logger import log

from modules.Tex.core.tex_compile import colourscheme_hex
from modules.Typst.module import typst_module as module
from modules.Typst.resources import (
    default_preamble,
    extra_font_paths,
    importable_resources,
    staging_root,
    typst_script_path,
)

"""
Provides a single context utility to compile Typst code from a user and return any error message
"""

__location__ = str(Path(__file__).resolve().parent)


def typst_colour(hexcode: str) -> str:
    """
    Convert a raw hex colour (or "trans") from `colourscheme_hex` into a Typst colour expression.
    """
    if hexcode == "trans":
        return "rgb(0, 0, 0, 0)"
    return f'rgb("#{hexcode}")'


# The format of the source to compile.
to_compile: str = """
#set page(width: 148mm, height: 210mm, margin: 10pt, fill: {bgcolour})
#set text(fill: {textcolour})
{preamble}
#import "typograph.typ": apply-fc
#show: apply-fc
{source}
"""


async def _run_typst_compile(
    ctx: Context,
    source: str,
    targetid: str,
    *,
    preamble: str = default_preamble,
    colour: str = "default",
):
    """
    Shared staging/rendering/compilation logic for `maketypst`.
    """
    log(
        "Beginning Typst compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"{staging_root}/{targetid}"

    # Remove the staging directory, if it exists
    await anyio.to_thread.run_sync(functools.partial(shutil.rmtree, path, ignore_errors=True))

    # Recreate staging directory
    await AsyncPath(path).mkdir(parents=True, exist_ok=True)

    # Make the shared .typ resources importable by filename from this staging directory,
    # since typst sandboxes file access to --root (the staging directory itself).
    for resource in importable_resources:
        await anyio.to_thread.run_sync(shutil.copy, resource, path)

    fn = AsyncPath(f"{path}/{targetid}.typ")

    bg_hex, text_hex = colourscheme_hex.get(colour, colourscheme_hex["default"])
    content = to_compile.format(
        bgcolour=typst_colour(bg_hex),
        textcolour=typst_colour(text_hex),
        preamble=preamble,
        source=source,
    )

    await fn.write_text(content)

    # Build compile script
    script = (
        f'{typst_script_path} {targetid} "{staging_root}" "{bg_hex}" "{text_hex}" "{extra_font_paths}" || exit;\n'
        f"cd {path}\n"
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def maketypst(
    ctx: Context,
    source: str,
    targetid: str,
    preamble: str = default_preamble,
    colour: str = "default",
):
    return await _run_typst_compile(ctx, source, targetid, preamble=preamble, colour=colour)


@module.init_task
def setup_typst_structure(client):
    """
    Set up the initial typst staging directory structure.
    """
    shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True, exist_ok=True)
