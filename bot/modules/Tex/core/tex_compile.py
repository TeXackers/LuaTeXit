import logging
import os
import shutil

from cmdClient import Context
from logger import log
from utils import ctx_addons  # noqa

from ..module import latex_module as module
from ..resources import (
    default_preamble,
    failed_image_path,
    lualatex_script_path,
    luatex_script_path,
    pdflatex_script_path,
    pdftex_script_path,
    pythontex_script_path,
    xelatex_script_path,
)

"""
Provides a single context utility to compile LaTeX code from a user and return any error message
"""

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def gencolour(colour, negate=True):
    """
    Build the colour conversion command for the provided colour, negating black text if required
    """
    return r"magick convert {{image}} {} -bordercolor transparent -border 50 \
        -background {} -flatten {{image}}".format(
        "-channel RGB +negate" if negate else "", colour
    )


# Dictionary of valid colours and the associated transformation commands
colourschemes = {
    "default": gencolour("'rgb(255, 255, 255)'", False),
    # New Discord UI colours
    "light": gencolour("'rgb(251, 251, 251)'", False),
    "ash": gencolour("'rgb(51, 51, 57)'", True),
    "dark": gencolour("'rgb(29, 29, 33)'", True),
    'onyx': gencolour("'rgb(0, 0, 0)'", True),
    # Make the old colours adaptive to the new UI
    "white": gencolour("'rgb(255, 255, 255)'", False),
    "grey": gencolour("'rgb(51, 51, 57)'", True), # ash
    "gray": gencolour("'rgb(51, 51, 57)'", True), # ash
    "darkgrey": gencolour("'rgb(29, 29, 33)'", True), # dark
    "darkgray": gencolour("'rgb(29, 29, 33)'", True), # dark
    "black": gencolour("'rgb(0, 0, 0)'", True), # onyx
    # Trans colours
    "transparent": r"magick {image} -channel RGB +negate -bordercolor transparent -border 40 {image}",
    "trans_white": r"magick {image} -channel RGB +negate -bordercolor transparent -border 40 {image}",
    "trans_black": None,
}

# Script which pads images to a minimum width of 1000
# pad_script = ""
pad_script = r"""
width=`magick convert {image} -format "%[fx:w]" info:`
minwidth=1000
extra=$((minwidth-width))

if [ $extra -gt 0 ]; then
    magick convert {image} \
        -gravity East +antialias -splice ${{extra}}x\
        -alpha set -background transparent -alpha Background -channel alpha -fx "i>${{width}}-5?0:a" +channel {image} >>/dev/null
fi
"""

# Header for every LaTeX source file
header: str = r"""

\protected\def\texitemote#1#2#3{%
    \relax\ifmmode
        \mathchoice
            {\texitemoteA{#1}{#2}{#3}{\texitemoteB6\textfont}{.4\texitemoteB5\textfont}}%
            {\texitemoteA{#1}{#2}{#3}{\texitemoteB6\textfont}{.4\texitemoteB5\textfont}}%
            {\texitemoteA{#1}{#2}{#3}{.7\texitemoteB6\scriptfont}\z@}%
            {\texitemoteA{#1}{#2}{#3}{.7\texitemoteB6\scriptscriptfont}{.1\texitemoteB5\scriptscriptfont}}%
    \else
        \leavevmode
        \texitemoteA{#1}{#2}{#3}{1em}{.4ex}%
    \fi
}
\def\texitemoteA#1#2#3#4#5{%
    \IfFileExists{#3}{%
        \lower#5\hbox{%
            \pdfximage width#4 #2{#3}%
            \pdfrefximage\pdflastximage
        }%
    }{%
        \lower#5\hbox to#4{\vrule \vbox to#4{\hsize=\dimexpr#4-.8\p@
            \hrule \vfil \centering \texit@debugfontbold #1\vfil \hrule
        }\vrule}%
    }%
}
\def\texitemoteB#1#2{\fontdimen#1#2\ifnum\fam=\m@ne \@ne\else \fam\fi}
\def\texitemotepasted{2025-10-28}
"""

# The format of the source to compile
to_compile: str = """{header}
{preamble}
\\begin{{document}}
{source}
\\end{{document}}"""


to_compile_plaintex: str = """
\\catcode`\\@=11

\\voffset=-1in
\\hoffset=-1in

\\hsize=300pt
\\parindent=\\z@

\\newdimen\\pagemargin \\pagemargin=10pt
\\newdimen\\textwidth \\textwidth=\\hsize
\\newdimen\\textheight \\textheight=\\vsize
\\let\\pdfpagewidth\\textwidth
\\let\\pageheight\\textheight
\\let\\pdfpageheight\\textheight
\\let\\pagewidth\\textwidth
\\newskip\\smallskipamount \\smallskipamount=3.0pt plus 1.0pt minus 1.0pt
\\newskip\\medskipamount \\medskipamount=6.0pt plus 2.0pt minus 2.0pt
\\newskip\\bigskipamount \\bigskipamount=12.0pt plus 4.0pt minus 4.0pt

\\output={{\\texitoutput}}
\\def\\texitoutput{{%
    \\setbox\\z@\\vbox{{%
        \\kern\\pagemargin
        \\hbox{{\\kern\\pagemargin \\pagebody \\kern\\pagemargin}}
        \\kern\\pagemargin
    }}
    \\pageheight\\ht\\z@
    \\pagewidth\\wd\\z@
    \\shipout\\box\\z@
}}
\\def\\pagebody{{\\vbox{{%
    \\unvbox\\@cclv \\unskip
    \\setbox\\z@=\\lastbox
    \\nointerlineskip \\hbox{{\\unhbox\\z@ \\/}}%
}}}}

\\catcode`\\@=12
{source}
\\bye"""


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
        level=logging.DEBUG,
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
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=pdflatex_script_path,
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
        level=logging.DEBUG,
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
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=lualatex_script_path,
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
        level=logging.DEBUG,
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
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=xelatex_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def make_plain_luatex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    # header=header,
    pad=True,
):
    log(
        "Beginning plain LuaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.DEBUG,
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
        work.write(to_compile_plaintex.format(source=source))
        work.close()

    # Build compile script
    script = (
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=luatex_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def make_plain_pdftex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    # header=header,
    pad=True,
):
    log(
        "Beginning plain pdfTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.DEBUG,
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
        work.write(to_compile_plaintex.format(source=source))
        work.close()

    # Build compile script
    script = (
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=pdftex_script_path,
            id=targetid,
            path=path,
            colour=colourschemes[colour] or "",
            pad=pad_script if pad else "",
        ).format(image="{}.png".format(targetid))
    )

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def makepythontex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    # header=header,
    pad=True,
):
    log(
        "Beginning pythonTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join(("\t" + line for line in source.splitlines())),
        ),
        level=logging.DEBUG,
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
        "{script} {id} || exit;\n"
        "cd {path}\n"
        "{colour}\n"
        "{pad}".format(
            script=pythontex_script_path,
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
