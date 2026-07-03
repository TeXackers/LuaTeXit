from typing import ClassVar

from cmdClient import cmdClient  # noqa

from modules.Tex.core.tex_utils import AutoTexLevel, TexNameStyle
from modules.Tex.module import latex_module as module

from . import (
    LatexUserSetting,
)


class LatexUser:
    # User configuration settings
    settings: ClassVar[dict] = {
        "autotex": LatexUserSetting.autotex,
        "keepsourcefor": LatexUserSetting.keepsourcefor,
        "colour": LatexUserSetting.colour,
        "alwaysmath": LatexUserSetting.alwaysmath,
        "alwayswide": LatexUserSetting.alwayswide,
        "namestyle": LatexUserSetting.namestyle,
        "autotex_level": LatexUserSetting.autotex_level,
    }

    __slots__ = (*settings.keys(), "id", "preamble")

    # Stored client for accessing data interfaces
    _client: ClassVar[None | cmdClient] = None

    def __init__(self, uid):
        self.id = uid

        # Explicitly typed user configuration settings
        self.autotex: bool = False
        self.keepsourcefor: int = 300
        self.colour: str = "light"
        self.alwaysmath: bool = False
        self.alwayswide: bool = False
        self.namestyle: TexNameStyle = TexNameStyle.NICKNAME
        self.autotex_level: AutoTexLevel = AutoTexLevel.WEAK

        self.preamble: str | None = None

        # Load the config from data
        self.load()

    def load(self):
        """
        Retrieve the user data from the database
        """
        # Get base config
        rows = self._client.data.user_latex_config.select_where(userid=self.id)
        for name, setting in self.settings.items():
            value = setting._data_to_value(
                self._client,
                self.id,
                setting.default if not rows or rows[0][name] is None else rows[0][name],
            )
            setattr(self, name, value)

        # Get preamble
        rows = self._client.data.user_latex_preambles.select_where(userid=self.id)
        if rows:
            self.preamble = rows[0]["preamble"] or self.preamble

    def get_setting_data(self, name: str):
        """
        Convenience method to retrieve the data for the requested setting.
        """
        if name not in self.settings:
            raise ValueError(f"Requested setting `{name}` does not exist.")

        setting = self.settings[name]
        value = getattr(self, name)

        return setting._data_from_value(self._client, self.id, value)

    @classmethod
    def get(cls, uid):
        return cls(uid)


@module.data_init_task
def attach_latexuser_client(client: cmdClient):
    LatexUser._client = client
