import functools
import logging
import re
import shutil

import anyio.to_thread
from anyio import Path as AsyncPath
from cmdClient import Context
from logger import log

from modules.Code.module import code_module as module
from modules.Code.resources import python_script_path, r_script_path, staging_root

"""
Provides a single context utility to run code from a user and return its captured output.
"""

# Marker the compiler scripts append after their captured output, so the exit
# code can travel back through `run_in_shell`'s single stdout string.
_EXIT_MARKER_RE = re.compile(r"__CODE_EXIT_(\d+)__\Z")

# Per-language staging/execution configuration.
LANG_CONFIG: dict[str, dict] = {
    "python": {
        "ext": "py",
        "script": python_script_path,
        # matplotlib needs a non-interactive backend selected before pyplot is imported.
        # `show()` can't do anything on Agg, so make it a silent no-op instead of letting
        # it warn -- users will naturally write it out of habit.
        "preamble": (
            "import matplotlib\n"
            'matplotlib.use("Agg")\n'
            "import matplotlib.pyplot as _code_plt\n"
            "_code_plt.show = lambda *_a, **_kw: None\n\n"
        ),
        # Save every figure the user's code left open, if any, numbering them in
        # creation order so a script producing several plots keeps them all.
        "postamble": (
            "\n\nfor _code_i, _code_fignum in enumerate(_code_plt.get_fignums(), start=1):\n"
            '    _code_plt.figure(_code_fignum).savefig("{output_path}" % _code_i, bbox_inches="tight", dpi=300)\n'
        ),
    },
    "r": {
        "ext": "R",
        "script": r_script_path,
        # Redirect the graphics device to a file so any plotting call (base R, ggplot2's
        # auto-print, etc.) during execution is captured, without the user needing to
        # call ggsave()/dev.off() themselves. The `%03d` in the filename is substituted
        # by the png() device itself, so each new plot page (each top-level auto-printed
        # ggplot object counts as one) is saved to its own numbered file instead of the
        # device just overwriting a single file on every page.
        "preamble": 'png(filename = "{output_path}", width = 8, height = 5, units = "in", res = 300)\n\n',
        "postamble": "\n\ninvisible(dev.off())\n",
    },
}


async def _run_code(ctx: Context, source: str, lang: str, targetid: str) -> tuple[str, bool]:
    """
    Shared staging/execution logic for `runcode`.

    Returns
    -------
    tuple[str, bool]:
        The captured stdout/stderr output (may be empty), and whether execution succeeded.
    """
    config = LANG_CONFIG[lang]
    log(
        "Running {lang} exec for (tid:{targetid}).\n{content}".format(
            lang=lang,
            targetid=targetid,
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"{staging_root}/{targetid}"

    # Remove the staging directory, if it exists, then recreate it
    await anyio.to_thread.run_sync(functools.partial(shutil.rmtree, path, ignore_errors=True))
    await AsyncPath(path).mkdir(parents=True, exist_ok=True)

    # `%03d` is substituted with the page number by R's png() device, or by the loop
    # in the Python postamble, so a script producing multiple plots keeps every one
    # instead of only the last.
    image_pattern = f"{path}/{targetid}_%03d.png"
    fn = AsyncPath(f"{path}/{targetid}.{config['ext']}")

    content = (
        config["preamble"].format(output_path=image_pattern)
        + source
        + config["postamble"].format(output_path=image_pattern)
    )
    await fn.write_text(content)

    # Build and run the execution script
    script = f'{config["script"]} {targetid} "{staging_root}"'
    raw = await ctx.run_in_shell(script)

    marker = _EXIT_MARKER_RE.search(raw)
    if marker is None:
        # The script didn't complete far enough to print its exit marker
        return raw, False

    output = raw[: marker.start()].rstrip()
    success = marker.group(1) == "0"

    # Strip filename so only the traceback itself is shown.
    friendly_name = f"script.{config['ext']}"
    output = output.replace(f"{path}/", "").replace(f"{targetid}.{config['ext']}", friendly_name)

    return output, success


@Context.util
async def run_code(ctx: Context, source: str, lang: str, targetid: str) -> tuple[str, bool]:
    return await _run_code(ctx, source, lang, targetid)


@module.init_task
def setup_code_structure(client):
    """
    Set up the initial code staging directory structure.
    """
    shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True, exist_ok=True)