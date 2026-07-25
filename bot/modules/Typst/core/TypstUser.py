from typing import ClassVar

from cmdClient import cmdClient  # noqa
from registry import Column, ColumnType, tableInterface, tableSchema
from settings import Boolean

from modules.Tex.core.LatexUserSetting import LatexUserSetting, colour, namestyle
from modules.Typst.module import typst_module as module

user_preamble_schema = tableSchema(
    "user_typst_preambles",
    Column("userid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("preamble", ColumnType.TEXT, primary=False, required=False),
)

user_config_schema = tableSchema(
    "user_typst_config",
    Column("userid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("autotypst", ColumnType.BOOL, primary=False, required=False),
)


class autotypst(LatexUserSetting, Boolean):
    """
    Typst-only setting not shared with LaTeX/
    """

    name = "autotypst"
    desc = "Whether to automatically compile typst codeblocks in your messages."

    default = False
    _outputs: ClassVar[dict[bool, str]] = {
        True: "Enabled (may be restricted by guild settings)",
        False: "Disabled (may be overriden by guild settings)",
    }

    _parsing_failed_response = "Unknown option `{userstr}`.\nPlease use `on` or `off`."

    _data_column = "autotypst"

    @classmethod
    def save(cls, client, userid, data):
        client.data.user_typst_config.upsert(constraint=cls._upsert_constraint, userid=userid, autotypst=data)
        if userid in TypstUser.cached_users:
            TypstUser.cached_users[userid].load()

    @classmethod
    def response(cls, ctx, data):
        match data:
            case True:
                return (
                    "I will now compile codeblocks with `typst` in your messages! "
                    "Be aware that automatic compilation may be "
                    "restricted by other guild and personal settings."
                )
            case False:
                return (
                    "You have disabled personal automatic compilation! "
                    "Codeblocks will still be automatically compiled "
                    "in guilds with the `typst` setting enabled."
                )
            case None:
                return "Unset `autotypst`!"


class TypstUser:
    """
    Cache of a Discord user's personal Typst preamble and configuration.

    `namestyle` and `colour` are shared with LaTeX so they're read from and
    written to the same `user_latex_config` table/settings LatexUser uses, so a
    user only has to set their preferred name display and output colourscheme
    once and it applies to both.
    """

    settings: ClassVar[dict] = {
        "autotypst": autotypst,
        "namestyle": namestyle,
        "colour": colour,
    }

    __slots__ = (*settings.keys(), "id", "preamble")

    # Cache of all users the client requests
    cached_users: ClassVar[dict] = {}

    # Stored client for accessing data interfaces
    _client: ClassVar[cmdClient | None] = None

    def __init__(self, uid):
        self.id = uid
        self.preamble: str | None = None

        self.load()

    def load(self):
        """
        Retrieve the user's preamble and configuration from the database.
        """
        # Typst-only settings
        rows = self._client.data.user_typst_config.select_where(userid=self.id)
        row = rows[0] if rows else None
        setting = self.settings["autotypst"]
        self.autotypst = setting._data_to_value(
            self._client,
            self.id,
            setting.default if not row or row["autotypst"] is None else row["autotypst"],
        )

        # Settings shared with LaTeX, read from `user_latex_config`
        rows = self._client.data.user_latex_config.select_where(userid=self.id)
        row = rows[0] if rows else None
        for name in ("namestyle", "colour"):
            setting = self.settings[name]
            value = setting._data_to_value(
                self._client,
                self.id,
                setting.default if not row or row[name] is None else row[name],
            )
            setattr(self, name, value)

        # Preamble
        rows = self._client.data.user_typst_preambles.select_where(userid=self.id)
        self.preamble = rows[0]["preamble"] if rows else None

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
        if uid not in cls.cached_users:
            cls.cached_users[uid] = cls(uid)
        return cls.cached_users[uid]


def set_user_preamble(client, userid, preamble):
    """
    Write a user's preamble, then refresh their cached `TypstUser` (if one exists)
    so it doesn't keep serving the stale preamble.
    """
    client.data.user_typst_preambles.insert(allow_replace=True, userid=userid, preamble=preamble)
    if userid in TypstUser.cached_users:
        TypstUser.cached_users[userid].load()


@module.data_init_task
def attach_typstuser_data(client: cmdClient):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, user_preamble_schema, shared=True),
        "user_typst_preambles",
    )
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, user_config_schema, shared=True),
        "user_typst_config",
    )
    TypstUser._client = client


# Register with LatexUserSetting so that changing a *shared* setting (namestyle,
# colour) through the LaTeX side also refreshes any cached TypstUser, and vice
# versa. See `LatexUserSetting._linked_user_caches`.
LatexUserSetting._linked_user_caches.append(TypstUser)
