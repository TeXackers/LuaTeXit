# LuaTeXit
LuaTeXit is a Discord.py bot coded by `@leothelion_` for enhanced LaTeX experience on Discord.

## Features
LuaTeXit started as a fork of Paradox/TeXit, but has since diverged significantly, with special attention towards TeX compilation commands and other quirks.

- Multiple TeX compilers, rather than a single hardcoded one. This addresses limitations pertaining to encoding, font selection, and ease of language support (especially non-ASCII, e.g. CJK):
  - `pdftex` / `pdf` — pdfLaTeX
  - `luatex` / `lua` — LuaLaTeX (default)
  - `plainlua` — plain LuaTeX
  - `plainpdf` / `pdfplain` — plain pdfTeX
  - `pytex` / `python` — LuaLaTeX + PythonTeX
  - `xetex` / `xelatex` — XeLaTeX (currently disabled)

- [Typst](https://typst.app)-related commands
- Preamble management, so servers can submit, review and reuse shared preambles.
- GitHub lookups on repositories and issues.
- Assortment of utility/fun commands: run `help` in Discord for the full list.

## Getting started
See [`config/README.md`](config/README.md) for instructions on how to configure and run your own instance.

## Support
LuaTeXit has a support guild, which also doubles as a development hub and a community to chat with and make friends! You can join the support guild [here](https://discord.gg/6xmCqddayY).

## Documentation
General wiki can be found at the [wiki](https://github.com/TeXackers/luatexit/wiki) of this repository. Otherwise you can use the `help` command to get a list of commands and their usage.
