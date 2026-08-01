from enum import Enum
from typing import Any, ClassVar

import discord
from cmdClient import Context, cmdClient
from cmdClient.lib import SafeCancellation

from settings.GuildSetting import GuildSetting

from .errors import BadUserInput

"""
Mixins for guild settings that provide converter methods for common types.

Setting types will typically only implement the converters and the `accepts` string.
Some setting types offer "configuration" via class attributes.
"""


class SettingType:
    """
    Abstract class representing a setting type.
    Intended to be used as a mixin for a GuildSetting,
    with the provided methods implementing converter methods for the setting.
    """

    accepts: ClassVar[str | None] = None  # User readable description of the acceptable values

    # Raw converters
    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value, **kwargs):
        """
        Convert a high-level setting value to internal data.
        """
        raise NotImplementedError

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: Any, **kwargs):
        """
        Convert internal data to high-level setting value.
        """
        raise NotImplementedError

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Parse user provided input into internal data.
        """
        raise NotImplementedError

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: Any, **kwargs):
        """
        Convert internal data into a formatted user-readable string.
        """
        raise NotImplementedError


class Boolean(SettingType):
    """
    Boolean type, supporting truthy and falsey user input.
    Configurable to change truthy and falsey values, and the output map.

    Types:
        data: bool | None
            The stored boolean value.
        value: bool | None
            The stored boolean value.
    """

    accepts = "Yes/No, On/Off, True/False, Enabled/Disabled"

    # Values that are accepted as truthy and falsey by the parser
    _truthy: ClassVar[frozenset[str]] = frozenset({"yes", "true", "on", "enable", "enabled"})
    _falsey: ClassVar[frozenset[str]] = frozenset({"no", "false", "off", "disable", "disabled"})

    # The user-friendly output strings to use for each value
    _outputs: ClassVar[dict[bool, str]] = {True: "On", False: "Off"}

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: bool | None, **kwargs):
        """
        Both data and value are of type bool | None.
        Directly return the provided value as data.
        """
        return value

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: bool | None, **kwargs):
        """
        Both data and value are of type bool | None.
        Directly return the internal data as the value.
        """
        return data

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Looks up the provided string in the truthy and falsey tables.
        """
        _userstr = userstr.lower()
        if _userstr == "none":
            return None
        if _userstr in cls._truthy:
            return True
        if _userstr in cls._falsey:
            return False
        raise BadUserInput(f"Unknown boolean type `{userstr}`")

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: bool | None, **kwargs):
        """
        Pass the provided value through the outputs map.
        """
        if data is None:
            return None
        return cls._outputs[data]


class Integer(SettingType):
    """
    Integer type. Storing any integer.

    Types:
        data: int | None
            The stored integer value.
        value: int | None
            The stored integer value.
    """

    accepts = "An integer."

    # Set limits on the possible integers
    _min = -4096
    _max = 4096

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: bool | None, **kwargs):
        """
        Both data and value are of type int | None.
        Directly return the provided value as data.
        """
        return value

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: bool | None, **kwargs):
        """
        Both data and value are of type int | None.
        Directly return the internal data as the value.
        """
        return data

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Relies on integer casting to convert the user string
        """
        if userstr.lower() == "none":
            return None

        try:
            num = int(userstr)
        except ValueError:
            raise BadUserInput("Couldn't parse provided integer.") from None

        if num > cls._max:
            raise BadUserInput("Provided integer was too large!")
        if num < cls._min:
            raise BadUserInput("Provided integer was too small!")

        return num

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Return the string version of the data.
        """
        if data is None:
            return None
        return str(data)


class String(SettingType):
    """
    String type, storing arbitrary text.
    Configurable to limit text length and restrict input options.

    Types:
        data: str | None
            The stored string.
        value: str | None
            The stored string.
    """

    accepts = "Any text"

    # Maximum length of string to accept
    _maxlen: int | None = None

    # Set of input options to accept
    _options: set | None = None

    # Whether to quote the string as code
    _quote: bool = True

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: str | None, **kwargs):
        """
        Return the provided value string as the data string.
        """
        return value

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: str | None, **kwargs):
        """
        Return the provided data string as the value string.
        """
        return data

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Check that the user-entered string is of the correct length.
        Accept "None" to unset.
        """
        if userstr.lower() == "none":
            # Unsetting case
            return None
        if cls._maxlen is not None and len(userstr) > cls._maxlen:
            raise BadUserInput(f"Provided string was too long! Maximum length is `{cls._maxlen}`")
        if cls._options is not None and userstr.lower() not in cls._options:
            raise BadUserInput("Invalid option! Valid options are `{}`".format("`, `".join(cls._options)))
        return userstr

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: str, **kwargs):
        """
        Wrap the string in backtics for formatting.
        Handle the special case where the string is empty.
        """
        if data:
            return f"`{data}`" if cls._quote else str(data)
        return None


class IntegerEnum(SettingType):
    """
    Integer Enum type, accepting limited strings, storing an integer, and returning an IntEnum value

    Types:
        data: int | None
            The stored integer.
        value: Any | None
            The corresponding Enum member
    """

    accepts = "A valid option."

    # Enum to use for mapping values
    _enum: type[Enum] | None = None

    # Custom map to format the value. If None, uses the enum names.
    _output_map = None

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: Any | None, **kwargs):
        """
        Return the value corresponding to the enum member
        """
        if value is not None:
            return value.value
        return None

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Return the enum member corresponding to the provided integer
        """
        if data is not None:
            return cls._enum(data)
        return None

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Find the corresponding enum member's value to the provided user input.
        Accept "None" to unset.
        """
        userstr = userstr.lower()

        options = {name.lower(): mem.value for name, mem in cls._enum.__members__.items()}

        if userstr == "none":
            # Unsetting case
            return None
        if userstr not in options:
            raise BadUserInput("Invalid option!")
        return options[userstr]

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: int, **kwargs):
        """
        Format the data using either the `_enum` or the provided output map.
        """
        if data is not None:
            value = cls._enum(data)
            if cls._output_map:
                return cls._output_map[value]
            return value.name
        return None


class Member(SettingType):
    """
    Member type, storing a single `discord.Member`.

    Types:
        data: int | None
            The user id of the stored Member.
        value: discord.Member | None
            The stored Member, or None if the member was not found.
    """

    accepts = "Member mention/id/name. Use 'None' to clear the setting."

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: discord.Member | None, **kwargs):
        """
        Returns the member id.
        """
        return value.id if value is not None else None

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Uses the client to look up the guild and member.
        Returns the Member if found, otherwise None.
        """
        # Always passthrough None
        if data is None:
            return None

        # Search for the member
        member = None
        guild = client.get_guild(guildid)
        if guild is not None:
            member = guild.get_member(data)

        return member

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Pass to the member seeker utility to find the requested member.
        Handle `0` and variants of `None` to unset.
        """
        if userstr.lower() in ("0", "none"):
            return None
        member = await ctx.find_member(userstr, interactive=True)
        if member is None:
            raise SafeCancellation
        return member.id

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Retrieve an artifically created user mention.
        """
        if data is None:
            return None
        return f"<@!{data}>"


class Role(SettingType):
    """
    Role type, storing a single `discord.Role`.
    Configurably allows returning roles which don't exist or are not seen by the client
    as `discord.Object`.

    Types:
        data: int | None
            The id of the stored Role.
        value: discord.Role | discord.Object | None
            The stored Role, or, if the role wasn't found and `_strict` is not set,
            a discord Object with the role id set.
    """

    accepts = "Role mention/id/name, or 'None' to unset"

    # Whether to disallow returning roles which don't exist as `discord.Object`s
    _strict = True

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: discord.Role | discord.Object | None, **kwargs):
        """
        Returns the role id.
        """
        return value.id if value is not None else None

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Uses the client to look up the guild and role id.
        Returns the role if found, otherwise returns a `discord.Object` with the id set,
        depending on the `_strict` setting.
        """
        # Always passthrough None
        if data is None:
            return None

        # Search for the role
        role = None
        guild = client.get_guild(guildid)
        if guild is not None:
            role = guild.get_role(data)

        if role is not None:
            return role
        if not cls._strict:
            return discord.Object(id=data)
        return None

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Pass to the role seeker utility to find the requested role.
        Handle `0` and variants of `None` to unset.
        """
        if userstr.lower() in ("0", "none"):
            return None
        role = await ctx.find_role(userstr, create=True, interactive=True)
        if role is None:
            raise SafeCancellation
        return role.id

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Retrieve the role name if found, otherwise the role id or None depending on `_strict`.
        """
        role = cls._data_to_value(client, guildid, data, **kwargs)
        if role is None:
            return None
        if isinstance(role, discord.Role):
            return role.mention
        return f"`{role.id}`"


class Channel(SettingType):
    """
    Channel type, storing a single `discord.Channel`.

    Types:
        data: int | None
            The id of the stored Channel.
        value: discord.abc.GuildChannel | None
            The stored Channel.
    """

    accepts = "Channel mention/id/name, or 'None' to unset"

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: discord.abc.GuildChannel | None, **kwargs):
        """
        Returns the channel id.
        """
        return value.id if value is not None else None

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Uses the client to look up the channel id.
        Returns the Channel if found, otherwise None.
        """
        # Always passthrough None
        if data is None:
            return None

        return client.get_channel(data)

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Pass to the channel seeker utility to find the requested channel.
        Handle `0` and variants of `None` to unset.
        """
        if userstr.lower() in ("0", "none"):
            return None
        channel = await ctx.find_channel(userstr, interactive=True)
        if channel is None:
            raise SafeCancellation
        return channel.id

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: int | None, **kwargs):
        """
        Retrieve an artifically created channel mention.
        If the channel does not exist, this will show up as invalid-channel.
        """
        if data is None:
            return None
        return f"<#{data}>"


class Emoji(SettingType):
    """
    Emoji type. Stores both custom and unicode emojis.
    """

    accepts = "Emoji, either built in or custom. Use 'None' to unset."

    @staticmethod
    def _parse_emoji(emojistr):
        """
        Converts a provided string into a PartialEmoji.
        If the string is badly formatted, returns None.
        """
        if ":" in emojistr:
            emojistr = emojistr.strip("<>")
            splits = emojistr.split(":")
            if len(splits) == 3:
                animated, name, eid = splits
                animated = bool(animated)
                return discord.PartialEmoji(name=name, animated=animated, id=int(eid))
        else:
            # TODO: Check whether this is a valid emoji
            return discord.PartialEmoji(name=emojistr)
        return None

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, value: discord.PartialEmoji | None, **kwargs):
        """
        Both data and value are of type discord.PartialEmoji | None.
        Directly return the provided value as data.
        """
        return value

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: discord.PartialEmoji | None, **kwargs):
        """
        Both data and value are of type discord.PartialEmoji | None.
        Directly return the internal data as the value.
        """
        return data

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Pass to the emoji string parser to get the emoji.
        Handle `0` and variants of `None` to unset.
        """
        if userstr.lower() in ("0", "none"):
            return None
        return cls._parse_emoji(userstr)

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: discord.PartialEmoji | None, **kwargs):
        """
        Return a string form of the partial emoji, which generally displays the emoji.
        """
        if data is None:
            return None
        return str(data)


# TODO: append and remove methods?
class SettingList(SettingType):
    """
    List of a particular type of setting.
    Note that this is an unusual setting type since it stores
    an empty list rather than None to clear a setting.

    The storage reader should never return None.

    Types:
        data: list[SettingType.data]
            List of data types of the specified SettingType.
            Some of the data may be None.
        value: list[SettingType.value]
            List of the value types of the specified SettingType.
            Some of the values may be None.
    """

    # Base setting type to make the list from
    _setting: type[SettingType | GuildSetting] = None

    # Whether 'None' values are filtered out of the data when creating values
    _allow_null_values: bool = False

    # Whether duplicate data values should be filtered out
    _force_unique: bool = False

    @classmethod
    def _data_from_value(cls, client: cmdClient, guildid: int, values: list[Any] | None, **kwargs):
        """
        Returns the setting type data for each value in the value list
        """
        if values is None:
            # Special behaviour here, store an empty list instead of None
            return []
        return [cls._setting._data_from_value(client, guildid, value) for value in values]

    @classmethod
    def _data_to_value(cls, client: cmdClient, guildid: int, data: list[Any] | None, **kwargs):
        """
        Returns the setting type value for each entry in the data list
        """
        if data is None:
            return []
        values = [cls._setting._data_to_value(client, guildid, entry) for entry in data]

        # Filter out null values if required
        if not cls._allow_null_values:
            values = [value for value in values if value is not None]
        return values

    @classmethod
    async def _parse_userstr(cls, ctx: Context, guildid: int, userstr: str, **kwargs):
        """
        Splits the user string across `,` to break up the list.
        Handle `0` and variants of `None` to unset.
        """
        if userstr.lower() in ("0", "none"):
            return []
        data = [await cls._setting._parse_userstr(ctx, guildid, item.strip()) for item in userstr.split(",")]

        if cls._force_unique:
            data = list(set(data))
        return data

    @classmethod
    def _format_data(cls, client: cmdClient, guildid: int, data: list[Any], **kwargs):
        """
        Format the list by adding `,` between each formatted item
        """
        if not data:
            return None
        formatted_items = []
        for item in data:
            formatted_item = cls._setting._format_data(client, guildid, item)
            if formatted_item is not None:
                formatted_items.append(formatted_item)
        return ", ".join(formatted_items)


class ChannelList(SettingList):
    """
    List of channels
    """

    accepts = "Comma separated list of channel mentions/ids/names. Use 'None' to unset."
    _setting = Channel


class RoleList(SettingList):
    """
    List of roles
    """

    accepts = "Comma separated list of role mentions/ids/names. Use 'None' to unset."
    _setting = Role


class MemberList(SettingList):
    """
    List of members
    """

    accepts = "Comma separated list of user mentions/ids/names. Use 'None' to unset."
    _setting = Member


class StringList(SettingList):
    """
    List of strings
    """

    accepts = "Comma separated list of strings. Use 'None' to unset."
    _setting = String
