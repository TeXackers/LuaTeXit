import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
HELP_FILE = os.path.join(__location__, "help.md")

with open(HELP_FILE, "r") as help_file:
    help_str = help_file.read()


info = {
    "dev_list": [220148284168077312],
    "info_str": (
        "I am primarily a LaTeX rendering bot coded in discord.py.\n"
        "Use `{prefix}help` for information on how to use me, "
        "and `{prefix}list` to see all my commands."
    ),
    # "invite_link": "https://discordapp.com/api/oauth2/authorize?client_id=871978350393065572&permissions=0&scope=bot",
    "invite_link": "Currently not accepting invites due to Discord's new policies.",
    "donate_link": "https://www.patreon.com/texit",
    "github": "https://github.com/texackers/LuaTeXit",
    "support_guild": "https://discord.gg/FY9jH7M",
    "brief": True,
    "app": "luatexit",
    "help_str": help_str,
    "help_file": "bot/resources/apps/luatexit/luatexit_thanks.png",
}

disabled_modules = ["Maths", "Starboard", "Social"]

disabled_commands = {
    # "colour",
    "echo",
    "emoji",
    "invitebot",
    "jumpto",
    "names",
    "piggybank",
    "quote",
    "secho",
}


def load_into(client):
    client.app_info = info

    for module in client.modules:
        if module.name in disabled_modules:
            module.enabled = False
        else:
            module.cmds = [
                cmd for cmd in module.cmds if cmd.name not in disabled_commands
            ]

    client.update_cmdnames()

    latex_module = [module for module in client.modules if module.name == "LaTeX"][0]

    latex_module.LatexGuild.defaults["autotex"] = True
    latex_setting = [
        setting for setting in latex_module.guild_settings if setting.name == "latex"
    ][0]
    latex_setting._default = True
