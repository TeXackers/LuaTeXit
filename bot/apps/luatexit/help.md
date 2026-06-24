# G'day {user.mention}!

I am a high quality LaTeX rendering and utility bot created to enhance LaTeX experience on Discord. Unlike my upstream TeXit, I focus more on catering the LuaLaTeX and XeLaTeX experience.

## LaTeX
- Unless LaTeX recognition has been disabled for a server, I shall attempt to recognise and render any LaTeX code you type automatically.
- The rendered output will be sent as a reply to your message, with `delete`, `show source/error`, `delete source` reaction options.
- Should any LaTeX errors occur, I shall make you aware that the code failed, which you can then click the `show source/error` reaction to view the error message and the source code that caused the error.

Commands:
```
{prefix}config latex enable/disable -- Enable or disable latex recognition for this server.
{prefix}luatex -- Manually render TeX code using LuaLaTeX.
{prefix}preamble -- Change your personal preamble (Define custom commands and add packages here)
{prefix}findfont -- Search for fonts in LuaTeXit's system for a given feature or features
{prefix}help tex -- See examples of use and all the options available
```

## Utility
Some of the utility features available:
```
{prefix}about -- View the current software and hardware versions 
{prefix}time -- Display your own time or that of another user (after setting your timezone)
```

## Fun
I also have commands which are purely for fun:
```
{prefix}8ball -- Ask 8ball a serious and important question
{prefix}roll -- Roll a DND-friendly die with a specified number of sides and rolls
```

Use `{prefix}list` to see all my commands and `{prefix}help cmd` to get detailed help for `cmd`.
If you still have any questions, requests, comments, or other feedback, please let us know with the `{prefix}feedback` command or join our friendly support server at {support}

Plus, you are always welcome to contribute: <{github}>

-# With love, LuaTeXit and the Team