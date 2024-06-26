import os
import shutil
import logging

from cmdClient import Context

from logger import log
from utils import ctx_addons  # noqa

from ..module import latex_module as module

from ..resources import (
    default_preamble,
    failed_image_path,
    compile_script_path,
    luatex_compile_script_path,
    xetex_compile_script_path,
)

"""
Provides a single context utility to compile LaTeX code from a user and return any error message
"""

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def gencolour(colour, negate=True):
    """
    Build the colour conversion command for the provided colour, negating black text if required
    """
    return r"convert {{image}} {} -bordercolor transparent -border 50 \
        -background {} -flatten {{image}}".format(
        "-channel RGB +negate" if negate else "", colour
    )


# Dictionary of valid colours and the associated transformation commands
colourschemes = dict()

colourschemes["white"] = gencolour("white", False)
colourschemes["black"] = gencolour("black")

colourschemes["light"] = gencolour("'rgb(233, 233, 233)'", False)
colourschemes["dark"] = gencolour("'rgb(20, 20, 20)'")

colourschemes["gray"] = colourschemes["grey"] = gencolour("'rgb(54, 57, 63)'")
colourschemes["darkgrey"] = gencolour("'rgb(35, 39, 42)'")

colourschemes[
    "trans_white"
] = r"convert {image} +negate -bordercolor transparent -border 40 {image}"
colourschemes["trans_black"] = None
colourschemes["transparent"] = colourschemes["trans_white"]

colourschemes["default"] = colourschemes["white"]

# Script which pads images to a minimum width of 1000
# pad_script = ""
pad_script = r"""
width=`convert {image} -format "%[fx:w]" info:`
minwidth=1000
extra=$((minwidth-width))

if [ $extra -gt 0 ]; then
    convert {image} \
        -gravity East +antialias -splice ${{extra}}x\
        -alpha set -background transparent -alpha Background -channel alpha -fx "i>${{width}}-5?0:a" +channel {image}
fi
"""

# Header for every LaTeX source file
header = """\\documentclass[varwidth, margin=2em,]{standalone}
\\IfFileExists{eggs.sty}{\\usepackage{eggs}}{}
\\ifpdftex\\usepackage{hwemoji}\\fi
"""

# The format of the source to compile
to_compile = """{header}
{preamble}
\\begin{{document}}
{source}
\\end{{document}}"""


@Context.util
async def maketex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    header=header,
    pad=True,
):
    log(
        "Beginning LaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.WARNING,
        context="mid:{}".format(ctx.msg.id) if ctx.msg else "tid:{}".format(targetid),
    )

    # Target's staging directory
    path = "tex/staging/{}".format(targetid)

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    os.makedirs(path, exist_ok=True)

    fn = "{}/{}.tex".format(path, targetid)

    with open(fn, "w") as work:
        work.write(to_compile.format(header=header, preamble=preamble, source=source))
        work.close()

    # Build compile script
    script = (
        "{compile_script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            compile_script=compile_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def makeluatex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    header=header,
    pad=True,
):
    log(
        "Beginning LuaLaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.WARNING,
        context="mid:{}".format(ctx.msg.id) if ctx.msg else "tid:{}".format(targetid),
    )

    # Target's staging directory
    path = "tex/staging/{}".format(targetid)

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    os.makedirs(path, exist_ok=True)

    fn = f"tex/staging/{targetid}/{targetid}.tex"

    with open(fn, "w") as work:
        work.write(to_compile.format(header=header, preamble=preamble, source=source))
        work.close()

    # Build compile script
    script = (
        "{compile_script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            compile_script=luatex_compile_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def makexetex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    header=header,
    pad=True,
):
    log(
        "Beginning XeLaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.WARNING,
        context="mid:{}".format(ctx.msg.id) if ctx.msg else "tid:{}".format(targetid),
    )

    # Target's staging directory
    path = "tex/staging/{}".format(targetid)

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    os.makedirs(path, exist_ok=True)

    fn = "{}/{}.tex".format(path, targetid)

    with open(fn, "w") as work:
        work.write(to_compile.format(header=header, preamble=preamble, source=source))
        work.close()

    # Build compile script
    script = (
        "{compile_script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            compile_script=xetex_compile_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@module.init_task
def setup_structure(client):
    """
    Set up the initial tex directory structure,
    including copying the required resources.
    """
    # Delete and recreate the staging directory, if it exists
    shutil.rmtree("tex/staging", ignore_errors=True)
    os.makedirs("tex/staging", exist_ok=True)
    shutil.copy(failed_image_path, "tex")
