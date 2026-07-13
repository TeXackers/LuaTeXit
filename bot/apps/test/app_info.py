from pathlib import Path

HELP_FILE = "apps/test/help.txt"

with Path.open(HELP_FILE) as help_file:
    help_str = help_file.read()


def load_into(bot):
    info = {
        "info_str": "Paradox test configuration.\nUse `{prefix}help` for information on how to use me, and `{prefix}list` to see all my commands!",
        "invite_link": "https://discordapp.com/api/oauth2/authorize?client_id=871978350393065572&permissions=0&scope=bot",
        "donate_link": "https://www.patreon.com/texit",
        "github": "https://github.com/texackers/LuaTeXit",
        "support_guild": "https://discord.gg/FY9jH7M",
        "brief": False,
        "app": "test",
        "help_str": help_str,
    }
    bot.objects.update(info)
