from pathlib import Path

from cmdClient import Module, cmdClient  # noqa

__location__ = Path(__file__).parent.resolve()
HELP_FILE = __location__ / "help.md"

with Path.open(HELP_FILE) as help_file:
    help_str = help_file.read()


info = {
    "info_str": (
        "I am primarily a LaTeX rendering bot coded in discord.py.\n"
        "Use `{prefix}help` for information on how to use me, "
        "and `{prefix}list` to see all my commands."
    ),
    "invite_link": "Currently not accepting invites due to Discord's new policies.",
    "donate_link": "https://www.patreon.com/texit",
    "github": "https://github.com/texackers/LuaTeXit",
    "support_guild": "https://discord.gg/FY9jH7M",
    "brief": True,
    "app": "luatexit",
    "help_str": help_str,
    "help_file": "bot/resources/apps/luatexit/luatexit_thanks.png",
}

disabled_modules = []

disabled_commands = {}


def load_into(client: cmdClient):
    client.app_info = info

    for module in client.modules:
        if module.name in disabled_modules:
            module.enabled = False
        else:
            module.cmds = [cmd for cmd in module.cmds if cmd.name not in disabled_commands]

    client.update_cmdnames()

    latex_module: Module = next(module for module in client.modules if module.name == "LaTeX")

    latex_module.LatexGuild.defaults["autotex"] = True
    latex_setting = next((setting for setting in latex_module.guild_settings if setting.name == "latex"), None)
    latex_setting.set_default(True)
