import logging
import shutil
from pathlib import Path

from cmdClient import Context
from logger import log

from modules.Tex.module import latex_module as module
from modules.Tex.resources import (
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

__location__ = str(Path(__file__).resolve().parent)


def gencolour(bgcolour: str, textcolour: str) -> str:
    """
    Build the colour definition commands for the provided colourscheme
    """
    return rf"pagecolor={bgcolour}, textcolor={textcolour}"


# Dictionary of valid colours and the associated transformation commands
colourschemes: dict = {
    "default": gencolour("ffffff", "000000"),
    # New Discord UI colours (in HEX)
    "light": gencolour("dfdfdf", "1d1d1d"),
    "ash": gencolour("323339", "DFDFDF"),
    "dark": gencolour("1A1A1E", "DFDFDF"),
    "onyx": gencolour("070709", "ffffff"),
    "white": gencolour("ffffff", "000000"),
    # Trans colours
    "transparent": gencolour("trans", "ffffff"),
    "trans_white": gencolour("trans", "ffffff"),
    "trans_black": gencolour("trans", "000000"),
}

# add alias names to colourschemes
colourschemes.update(
    {
        "grey": colourschemes["ash"],  # ash
        "darkgrey": colourschemes["dark"],  # dark
        "black": colourschemes["onyx"],  # onyx
    },
)

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
to_compile: str = """\\documentclass[12pt, singlepage, {colour}, {alwayswide}]{{texit}}
{header}
\\usepackage{{iftex}}
{preamble}
\\begin{{document}}
{source}
\\end{{document}}
"""


to_compile_plaintex: str = r"""
\catcode`\@=11

\voffset=-1in
\hoffset=-1in

\hsize=300pt
\parindent=\z@

\newdimen\pagemargin \pagemargin=10pt
\newdimen\textwidth \textwidth=\hsize
\newdimen\textheight \textheight=\vsize
\let\pdfpagewidth\textwidth
\let\pageheight\textheight
\let\pdfpageheight\textheight
\let\pagewidth\textwidth
\newskip\smallskipamount \smallskipamount=3.0pt plus 1.0pt minus 1.0pt
\newskip\medskipamount \medskipamount=6.0pt plus 2.0pt minus 2.0pt
\newskip\bigskipamount \bigskipamount=12.0pt plus 4.0pt minus 4.0pt

\output={{\texitoutput}}
\def\texitoutput{{%
    \setbox\z@\vbox{{%
        \kern\pagemargin
        \hbox{{\kern\pagemargin \pagebody \kern\pagemargin}}
        \kern\pagemargin
    }}
    \pageheight\ht\z@
    \pagewidth\wd\z@
    \shipout\box\z@
}}
\def\pagebody{{\vbox{{%
    \unvbox\@cclv \unskip
    \setbox\z@=\lastbox
    \nointerlineskip \hbox{{\unhbox\z@ \/}}%
}}}}

\catcode`\@=12
{source}
\bye"""


@Context.util
async def maketex(ctx, source, targetid, preamble=default_preamble, colour="default", header=header, pad=True):
    log(
        "Beginning LaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"{path}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile.format(
                colour=colourschemes[colour] or "",
                alwayswide="minpagewidth=110pt" if pad else "",
                header=header,
                preamble=preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{pdflatex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def makeluatex(ctx, source, targetid, preamble=default_preamble, colour="default", header=header, pad=True):
    log(
        "Beginning LuaLaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"tex/staging/{targetid}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile.format(
                colour=colourschemes[colour] or "",
                alwayswide="minpagewidth=110pt" if pad else "",
                header=header,
                preamble=preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{lualatex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def makexetex(ctx, source, targetid, preamble=default_preamble, colour="default", header=header, pad=True):
    log(
        "Beginning XeLaTeX compilation for (tid:{targetid}).\n{content}".format(
            targetid=targetid,
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"{path}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile.format(
                colour=colourschemes[colour] or "",
                alwayswide="minpagewidth=110pt" if pad else "",
                header=header,
                preamble=preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{xelatex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

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
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"{path}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile_plaintex.format(
                # colour = colourschemes[colour] or "",
                # alwayswide = "minpagewidth=110pt" if pad else "",
                # header = header,
                # preamble = preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{luatex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

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
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"{path}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile_plaintex.format(
                # colour = colourschemes[colour] or "",
                # alwayswide = "minpagewidth=110pt" if pad else "",
                # header = header,
                # preamble = preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{pdftex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

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
            content="\n".join("\t" + line for line in source.splitlines()),
        ),
        level=logging.DEBUG,
        context=f"mid:{ctx.msg.id}" if ctx.msg else f"tid:{targetid}",
    )

    # Target's staging directory
    path = f"tex/staging/{targetid}"

    # Remove the staging directory, if it exists
    shutil.rmtree(path, ignore_errors=True)

    # Recreate staging directory
    Path(path).mkdir(parents=True, exist_ok=True)

    fn: Path = Path(f"{path}/{targetid}.tex")

    with Path.open(fn, "w") as work:
        work.write(
            to_compile.format(
                colour=colourschemes[colour] or "",
                alwayswide="minpagewidth=110pt" if pad else "",
                header=header,
                preamble=preamble,
                source=source,
            ),
        )
        work.close()

    # Build compile script
    script = (f"{pythontex_script_path} {targetid} || exit;\ncd {path}\n").format(image=f"{targetid}.png")

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
    Path("tex/staging").mkdir(parents=True, exist_ok=True)
    shutil.copy(failed_image_path, "tex")
