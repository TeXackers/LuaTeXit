import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
HELP_FILE = os.path.join(__location__, "help.txt")

with open(HELP_FILE, "r") as help_file:
    help_str = help_file.read()


def load_into(client):
    info = {
        "dev_list": [220148284168077312],
        "info_str": (
            "I am a multi-purpose server automation bot written in discord.py.\n"
            "Use `{prefix}help` for information on how to use me, "
            "and `{prefix}list` to see all my commands!"
        ),
        "invite_link": "https://discordapp.com/api/oauth2/authorize?client_id=871978350393065572&permissions=0&scope=bot",
        "donate_link": "https://www.patreon.com/texit",
        "github": "https://github.com/ponte-vecchio/LuaTeXit",
        "support_guild": "https://discord.gg/FY9jH7M",
        "brief": False,
        "app": "",
        "help_str": help_str,
    }
    client.app_info = info
