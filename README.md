# LuaTeXit
LuaTeXit is a Discord.py bot coded by `@leothelion_` for enhanced LaTeX experience on Discord.

## Features
LuaTeXit is a fork of [Paradox/TeXit](https://gitlab.paradoxical.pw/team-paradox/paradox) (TeXit therein), with special attention towards TeX compilation commands.
A key distinguishing feature is the compiler option. TeXit to date uses `pdflatex` as its default and sole compiler. 
While this satisfies most use cases, it has brought on limitations pertaining to encoding, font selection, and ease of language support (especially non-ASCII, e.g., CJK). To address these limitations, LuaTeXit offers the following compilers:

| Compiler | Command | Under the hood |
| --- | --- | --- |
| pdfLaTeX | `pdftex` or `pdf` | `latexmk -pdf -file-line-error -halt-on-error %TEXFILE%` |
| LuaLaTeX | `luatex` or `lua` | `latexmk -lualatex -file-line-error -halt-on-error %TEXFILE%` |
| XeLaTeX | `xetex` | `latexmk -xelatex -file-line-error -halt-on-error %TEXFILE%` |
| primitive LuaTeX | `plaintex` or `plain` | `luatex -file-line-error -halt-on-error %TEXFILE%` |

# Support
LuaTeXit has a support guild, which also doubles as a develpo hub and a community to chat with and make friends! You can join the support guild [here](https://discord.gg/FY9jH7M).

# Documentation
General wiki can be found at the [wiki](https://github.com/ponte-vecchio/luatexit/wiki) of this repository. Otherwise you can use the `help` command to get a list of commands and their usage.
