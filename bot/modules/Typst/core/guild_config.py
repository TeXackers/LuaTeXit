from typing import ClassVar

from settings import Boolean, ColumnData, GuildSetting
from wards import guild_manager

from modules.Typst.module import typst_module as module

from .TypstGuild import TypstGuild


@module.guild_setting
class autotypst(ColumnData, Boolean, GuildSetting):
    attr_name = "autotypst"
    category = "Typst"
    read_check = None
    write_check = guild_manager

    name = "typst"
    desc = "Automatically compile Typst codeblocks."

    long_desc = (
        "When enabled, automatically detect and compile ```typst/```typ codeblocks in messages.\n"
        "Affected by personal configuration (see `autotypst`)."
    )

    _outputs: ClassVar[dict[bool, str]] = {True: "Enabled", False: "Disabled"}

    _default = TypstGuild.defaults["autotypst"]

    _table_interface_name = "guild_typst_config"
    _data_column = "autotypst"
    _delete_on_none = False

    def write(self, **kwargs):
        """
        Write data and update stored TypstGuild
        """
        super().write(**kwargs)
        TypstGuild.get(self.guildid).load()
