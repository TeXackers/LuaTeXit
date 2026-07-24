import functools
import logging
import shutil
from pathlib import Path

import anyio.to_thread
from anyio import Path as AsyncPath
from cmdClient import Context
from logger import log

from modules.Tex.module import latex_module as module
from modules.Tex.resources import (
    default_preamble,
    failed_dir,
    lualatex_script_path,
    luatex_script_path,
    pdflatex_script_path,
    pdftex_script_path,
    pythontex_script_path,
    staging_root,
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


# Pairs for each named colourscheme
colourscheme_hex: dict[str, tuple[str, str]] = {
    "default": ("ffffff", "000000"),
    # New Discord UI colours (in HEX)
    "light": ("dfdfdf", "1d1d1d"),
    "ash": ("323339", "DFDFDF"),
    "dark": ("1A1A1E", "DFDFDF"),
    "onyx": ("070709", "ffffff"),
    "white": ("ffffff", "000000"),
    # Trans colours
    "transparent": ("trans", "ffffff"),
    "trans_white": ("trans", "ffffff"),
    "trans_black": ("trans", "000000"),
}

# add alias names to colourscheme_hex
colourscheme_hex.update(
    {
        "grey": colourscheme_hex["ash"],  # ash
        "darkgrey": colourscheme_hex["dark"],  # dark
        "black": colourscheme_hex["onyx"],  # onyx
    },
)

# Dictionary of valid colours and the associated LaTeX transformation commands
colourschemes: dict = {name: gencolour(*hexes) for name, hexes in colourscheme_hex.items()}

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


async def _run_tex_compile(
    ctx: Context,
    source: str,
    targetid: str,
    engine_name: str,
    script_path: Path,
    *,
    plaintex: bool = False,
    preamble: str = default_preamble,
    colour: str = "default",
    header: str = header,
    pad: bool = True,
):
    """
    Shared staging/rendering/compilation logic used by all the engine-specific
    maketex* utils below; only the template, script and log label vary.
    """
    log(
        "Beginning {engine} compilation for (tid:{targetid}).\n{content}".format(
            engine=engine_name,
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

    fn = AsyncPath(f"{path}/{targetid}.tex")

    if plaintex:
        content = to_compile_plaintex.format(source=source)
    else:
        content = to_compile.format(
            colour=colourschemes[colour] or "",
            alwayswide="minpagewidth=110pt" if pad else "",
            header=header,
            preamble=preamble,
            source=source,
        )

    await fn.write_text(content)

    # Build compile script
    script = f'{script_path} {targetid} "{staging_root}" "{failed_dir}" || exit;\ncd {path}\n'

    # Run the script in an async executor
    return await ctx.run_in_shell(script)


@Context.util
async def maketex(
    ctx: Context,
    source: str,
    targetid: str,
    preamble: str = default_preamble,
    colour: str = "default",
    header: str = header,
    pad: bool = True,
):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "LaTeX",
        pdflatex_script_path,
        preamble=preamble,
        colour=colour,
        header=header,
        pad=pad,
    )


@Context.util
async def makeluatex(ctx, source, targetid, preamble=default_preamble, colour="default", header=header, pad=True):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "LuaLaTeX",
        lualatex_script_path,
        preamble=preamble,
        colour=colour,
        header=header,
        pad=pad,
    )


@Context.util
async def makexetex(ctx, source, targetid, preamble=default_preamble, colour="default", header=header, pad=True):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "XeLaTeX",
        xelatex_script_path,
        preamble=preamble,
        colour=colour,
        header=header,
        pad=pad,
    )


@Context.util
async def make_plain_luatex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    pad=True,
):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "plain LuaTeX",
        luatex_script_path,
        plaintex=True,
        preamble=preamble,
        colour=colour,
        pad=pad,
    )


@Context.util
async def make_plain_pdftex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    pad=True,
):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "plain pdfTeX",
        pdftex_script_path,
        plaintex=True,
        preamble=preamble,
        colour=colour,
        pad=pad,
    )


@Context.util
async def makepythontex(
    ctx,
    source,
    targetid,
    preamble=default_preamble,
    colour="default",
    pad=True,
):
    return await _run_tex_compile(
        ctx,
        source,
        targetid,
        "pythonTeX",
        pythontex_script_path,
        preamble=preamble,
        colour=colour,
        pad=pad,
    )


@module.init_task
def setup_structure(client):
    """
    Set up the initial tex directory structure.
    """
    # Delete and recreate the staging directory, if it exists
    shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True, exist_ok=True)
