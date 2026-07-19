from registry import Column, ColumnType, tableInterface, tableSchema
from settings import ColumnData, GuildSetting, String
from wards import fail_ward, guild_admin

from .module import maths_module as module


# Create setting interface
@module.guild_setting
class GuildWolfID(ColumnData, String, GuildSetting):
    """Permit the use of a custom Wolfram AppID for the `wolframalpha --full` command."""

    attr_name = "wolfram_id"
    category = "Misc"

    read_check = fail_ward
    write_check = guild_admin

    name = "wolfram_id"
    desc = "Custom wolfram AppID for the full-result `wolframalpha --full` command."

    long_desc = (
        "Custom wolfram application license token to run the full-result `wolframalpha --full` command.\n"
        "May be used to upgrade Wolfram queries to a different plan.\n"
        "A limited licence may be obtained for free "
        "[here](https://products.wolframalpha.com/api/documentation/#obtaining-an-appid).\n"
        "After obtaining, configure this setting with your `AppID`.\n"
        "*Do not expose your AppID to untrusted members.*"
    )

    _maxlen = 20

    _table_interface_name = "guild_wolfram_appid"
    _data_column = "appid"
    _delete_on_none = False


@module.guild_setting
class GuildWolfShortID(ColumnData, String, GuildSetting):
    """Permit the use of a custom Wolfram AppID for the default, short-answer `wolframalpha` command."""

    attr_name = "wolfram_short_id"
    category = "Misc"

    read_check = fail_ward
    write_check = guild_admin

    name = "wolfram_short_id"
    desc = "Custom wolfram AppID for the default short-answer `wolframalpha` command."

    long_desc = (
        "Custom wolfram application license token to run the default, short-answer `wolframalpha` command.\n"
        "This uses Wolfram's [Short Answers API]"
        "(https://products.wolframalpha.com/short-answers-api/documentation), which requires its own AppID, "
        "separate from the full-result `wolfram_id`.\n"
        "After obtaining, configure this setting with your `AppID`.\n"
        "*Do not expose your AppID to untrusted members.*"
    )

    _maxlen = 20

    _table_interface_name = "guild_wolfram_appid"
    _data_column = "short_appid"
    _delete_on_none = False


@module.guild_setting
class GuildWolfInstaCalcID(ColumnData, String, GuildSetting):
    """Permit the use of a custom Wolfram AppID for the `wolframalpha` command's Instant Calculation lookups."""

    attr_name = "wolfram_instacalc_id"
    category = "Misc"

    read_check = fail_ward
    write_check = guild_admin

    name = "wolfram_instacalc_id"
    desc = "Custom wolfram AppID for the Instant Calculation API."

    long_desc = (
        "Custom wolfram application license token for Wolfram's Instant Calculation API.\n"
        "This requires its own AppID, separate from the full-result `wolfram_id` and "
        "short-answer `wolfram_short_id`.\n"
        "After obtaining, configure this setting with your `AppID`.\n"
        "*Do not expose your AppID to untrusted members.*"
    )

    _maxlen = 20

    _table_interface_name = "guild_wolfram_appid"
    _data_column = "instacalc_appid"
    _delete_on_none = False


# Define data schema
schema = tableSchema(
    "guild_wolfram_appid",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("appid", ColumnType.SHORTSTRING),
    Column("short_appid", ColumnType.SHORTSTRING),
    Column("instacalc_appid", ColumnType.SHORTSTRING),
)


# Attach data interface
@module.data_init_task
def attach_wolf_data(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, schema, shared=True),
        "guild_wolfram_appid",
    )
