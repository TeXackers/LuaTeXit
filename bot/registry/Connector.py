import logging
from itertools import chain
from typing import TYPE_CHECKING, Any

from logger import log

if TYPE_CHECKING:
    from .tableInterface import tableInterface


# TODO: Versioning
# TODO: is not null
# TODO: Documentation and interface examples
class Connector:
    """
    Abstract base class representing a high level database connector.
    """

    # Type of database we are connecting to, e.g. 'sqlite'
    db_type = None

    # Replace character the cursor formatter uses, e.g. '%s' or '?'
    replace_char = None

    # Arguments to pass to each cursor
    cursor_args = {}

    # The underlying DBAPI connection, set to a real connection object by subclasses
    conn: Any

    # Data interfaces attached at runtime via `attach_interface`, see modules'
    # `data_init_task` hooks for the attaching call sites.
    guild_latex_channels: "tableInterface"
    guild_latex_config: "tableInterface"
    guild_latex_preambles: "tableInterface"
    guild_typst_config: "tableInterface"
    user_latex_config: "tableInterface"
    user_latex_preambles: "tableInterface"
    user_pending_preambles: "tableInterface"
    user_time_settings: "tableInterface"
    user_typst_config: "tableInterface"
    user_typst_preambles: "tableInterface"

    def __init__(self, **dbopts):
        self.interfaces = {}  # Dict of attached data interfaces
        self.conn = None

    def close(self):
        """
        Close the connection
        """
        self.conn.close()

    def attach_interface(self, interface, name):
        """
        Attach a data interface to this connector.
        """
        log(f"  |-- {interface.__class__.__name__} --> {name}.", context="DATABASE", level=logging.DEBUG)
        setattr(self, name, interface)
        self.interfaces[name] = interface

    def get_schema(self):
        """
        Retrieve the combined creation schema for all interfaces.
        """
        # TODO: Some handling of dependencies
        # TODO: Name interfaces, add comments in schema
        return "\n\n".join(interface.schema for interface in self.interfaces.values())

    def format_conditions(self, conditions):
        """
        Formats a dictionary of conditions into a string suitable for 'WHERE' clauses.
        Supports `IN` type conditionals.
        """
        if not conditions:
            return ("", tuple())

        values = []
        conditional_strings = []
        for key, item in conditions.items():
            if isinstance(item, (list, tuple)):
                conditional_strings.append("{} IN ({})".format(key, ", ".join([self.replace_char] * len(item))))
                values.extend(item)
            else:
                conditional_strings.append(f"{key}={self.replace_char}")
                values.append(item)

        return (" AND ".join(conditional_strings), values)

    def format_updatestr(self, valuedict):
        """
        Formats a dictionary of keys and values into a string suitable for 'SET' clauses.
        """
        if not valuedict:
            return ("", tuple())
        keys, values = zip(*valuedict.items())

        set_str = ", ".join(f"{key} = {self.replace_char}" for key in keys)

        return (set_str, values)

    def format_selectkeys(self, keys):
        """
        Formats a list of keys into a string suitable for `SELECT`.
        """
        if not keys:
            return "*"
        return ", ".join(keys)

    def format_insertkeys(self, keys):
        """
        Formats a list of keys into a string suitable for `INSERT`
        """
        if not keys:
            return ""
        return "({})".format(", ".join(keys))

    def format_insertvalues(self, values):
        """
        Formats a list of values into a string suitable for `INSERT`
        """
        value_str = "({})".format(", ".join(self.replace_char for value in values))
        return (value_str, values)

    def select_where(self, table, select_columns=None, cursor=None, **conditions):
        """
        Select rows from the given table matching the conditions
        """
        criteria, criteria_values = self.format_conditions(conditions)
        col_str = self.format_selectkeys(select_columns)

        if conditions:
            where_str = f"WHERE {criteria}"
        else:
            where_str = ""

        cursor = cursor or self.conn.cursor(**self.cursor_args)
        cursor.execute(f"SELECT {col_str} FROM {table} {where_str}", criteria_values)
        return cursor.fetchall()

    def update_where(self, table, valuedict, cursor=None, **conditions):
        """
        Update rows in the given table matching the conditions
        """
        key_str, key_values = self.format_updatestr(valuedict)
        criteria, criteria_values = self.format_conditions(conditions)

        if conditions:
            where_str = f"WHERE {criteria}"
        else:
            where_str = ""

        cursor = cursor or self.conn.cursor(**self.cursor_args)
        cursor.execute(f"UPDATE {table} SET {key_str} {where_str}", tuple((*key_values, *criteria_values)))
        self.conn.commit()
        return cursor

    def delete_where(self, table, cursor=None, **conditions):
        """
        Delete rows in the given table matching the conditions
        """
        criteria, criteria_values = self.format_conditions(conditions)

        cursor = cursor or self.conn.cursor(**self.cursor_args)
        cursor.execute(f"DELETE FROM {table} WHERE {criteria}", criteria_values)
        self.conn.commit()
        return cursor

    def insert(self, table, cursor=None, allow_replace=False, **values):
        """
        Insert the given values into the table
        """
        keys, values = zip(*values.items())

        key_str = self.format_insertkeys(keys)
        value_str, values = self.format_insertvalues(values)

        action = "REPLACE" if allow_replace else "INSERT"

        cursor = cursor or self.conn.cursor(**self.cursor_args)
        cursor.execute(f"{action} INTO {table} {key_str} VALUES {value_str}", values)
        self.conn.commit()
        return cursor

    def insert_many(self, table, *value_tuples, insert_keys=None, cursor=None):
        """
        Insert all the given values into the table
        """
        key_str = self.format_insertkeys(insert_keys)
        value_strs, value_tuples = zip(*(self.format_insertvalues(value_tuple) for value_tuple in value_tuples))

        value_str = ", ".join(value_strs)
        values = tuple(chain(*value_tuples))

        cursor = cursor or self.conn.cursor(**self.cursor_args)
        cursor.execute(f"INSERT INTO {table} {key_str} VALUES {value_str}", values)
        self.conn.commit()
        return cursor

    def upsert(self, table, constraint, cursor=None, **values):
        """
        Insert or on conflict update.
        Conflict behaviour is to update the columns that were to be inserted.
        `constraint` is the constraint which fails.
        This may be ignored by some connectors (e.g. mysql), but is required by some connectors
        (e.g. Postgres, Sqlite.)
        """
        raise NotImplementedError

    def create_database(self):
        """
        Creates the database using the given schema.
        """
        raise NotImplementedError
