import logging

from paraModule import paraModule
from registry import Column, ColumnType, RawElement, tableInterface, tableSchema

"""
Define core shared data for paradoxical instances.
Specifically:
    Define the version table and check the current version matches.
"""

REQUIRED_DATA_VERSION = 3


# ------------------------------
# Version table and checker
# ------------------------------
raw_insert_line: str = (
    f"INSERT INTO VERSION (version, updated_by) VALUES ({REQUIRED_DATA_VERSION}, 'Initial Creation');"  # noqa
)

version_schema = tableSchema(
    "VERSION",
    Column("version", ColumnType.INT, required=True, primary=True),
    Column("updated_at", ColumnType.TIMESTAMP, default="CURRENT_TIMESTAMP", required=True),
    Column("updated_by", ColumnType.SHORTSTRING),
    RawElement(raw_insert_line, raw_insert_line),
    add_timestamp=False,
)

versionModule = paraModule(
    "version_table",
    description="Skeleton module which loads the version table and checks the version on startup.",
)


@versionModule.data_init_task
def load_version_table(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, version_schema, shared=True),
        "version",
    )


class DataVersionMismatch(Exception):
    """
    Custom exception class indicating the current data version is incorrect.
    """


@versionModule.init_task
def check_data_version(client):
    versions = client.data.version.select_where()
    if versions:
        version = max(row["version"] for row in versions)
        if version != REQUIRED_DATA_VERSION:
            client.log(
                "Refusing to start the client due to data version mismatch! "
                f"Current data version is `{version}`, required version is `{REQUIRED_DATA_VERSION}`. "
                "Shutting down the client.",
                level=logging.CRITICAL,
                context="DATA_VERSION",
            )
            raise DataVersionMismatch(
                f"Current version `{version}` not equal to required version `{REQUIRED_DATA_VERSION}`",
            )
        client.log(f"Data Version: {version}", context="DATA_VERSION", level=logging.DEBUG)
    else:
        client.log(
            "Refusing to start the client due to nonexistent version! "
            f"Required version is `{REQUIRED_DATA_VERSION}`, but no version was found in the database. "
            "Shutting down the client.",
            level=logging.CRITICAL,
            context="DATA_VERSION",
        )
        raise DataVersionMismatch(f"No version in database. Required version is `{REQUIRED_DATA_VERSION}`")
