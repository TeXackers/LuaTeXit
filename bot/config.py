import configparser as cfgp
from pathlib import Path

from paraEmoji import configEmoji

conf: Conf = None


class Conf:
    def __init__(self, configfile, section_name: str = "DEFAULT"):
        self.configfile = configfile

        self.config = cfgp.ConfigParser(
            converters={"intlist": self._getintlist, "list": self._getlist, "emoji": configEmoji.from_str},
        )
        self.config.read(configfile)

        self.section_name = section_name if section_name in self.config else "DEFAULT"

        self.default = self.config["DEFAULT"]
        self.section = self.config[self.section_name]
        self.emojis = self.config["EMOJIS"] if "EMOJIS" in self.config else self.section  # noqa

        # Config file recursion, read in configuration files specified in every "ALSO_READ" key.
        more_to_read = self.section.getlist("ALSO_READ", [])
        read = set()
        while more_to_read:
            to_read = more_to_read.pop(0)
            read.add(to_read)
            self.config.read(to_read)
            new_paths = [
                path for path in self.section.getlist("ALSO_READ", []) if path not in read and path not in more_to_read
            ]
            more_to_read.extend(new_paths)

        global conf
        conf = self

    def __getitem__(self, key):
        return self.section[key].strip()

    def __getattr__(self, name):
        return getattr(self.section, name)

    def get(self, name, fallback=None):
        result = self.section.get(name, fallback)
        return result.strip() if result else result

    def _getintlist(self, value):
        return [int(item.strip()) for item in value.split(",")]

    def _getlist(self, value):
        return [item.strip() for item in value.split(",")]

    def write(self):
        with Path(self.configfile).open("w") as conffile:
            self.config.write(conffile)


def get_conf():
    if conf is None:
        raise Exception("Retrieving configuration without initialisation.")
    return conf
