from typing import ClassVar

from cmdClient import cmdClient
from registry import Column, ColumnType, tableInterface, tableSchema

from modules.Typst.module import typst_module as module

guild_config_schema = tableSchema(
    "guild_typst_config",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("autotypst", ColumnType.BOOL, primary=False, required=False),
)


class TypstGuild:
    __slots__ = ("autotypst", "id")

    # Cache of all guilds the client requests
    cached_guilds: ClassVar[dict] = {}

    # Stored client for accessing data interfaces
    _client: ClassVar[cmdClient | None] = None

    # Defaults
    defaults: ClassVar[dict] = {
        "autotypst": False,
    }

    def __init__(self, uid):
        if self._client is None:
            raise RuntimeError("Attempted to get a TypstGuild before data initialisation.")

        self.id = uid

        # Whether typst codeblocks are automatically compiled
        self.autotypst: bool = False

        self.load()

    def load(self):
        """
        Retrieve the guild data from the database, handling the DM context (id 0) separately.
        """
        if self.id == 0:
            self.autotypst = True
            return

        self.autotypst = self.defaults["autotypst"]

        rows = self._client.data.guild_typst_config.select_where(guildid=self.id)
        if rows and rows[0]["autotypst"] is not None:
            self.autotypst = bool(rows[0]["autotypst"])

    @classmethod
    def get(cls, uid):
        if uid not in cls.cached_guilds:
            cls.cached_guilds[uid] = cls(uid)
        return cls.cached_guilds[uid]


module.TypstGuild = TypstGuild


@module.data_init_task
def attach_typstguild_data(client: cmdClient):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, guild_config_schema, shared=True),
        "guild_typst_config",
    )
    TypstGuild._client = client
