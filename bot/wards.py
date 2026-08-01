from cmdClient import check, Context  # noqa

from config import get_conf
from utils.cache import async_ttl_cache
from typing import TYPE_CHECKING

from discord import Member, TeamMemberRole

if TYPE_CHECKING:
    from discord import AppInfo, Team


@async_ttl_cache(days=7)
async def get_team_info(client, who: str) -> tuple[int | None, frozenset[int]]:
    """Fetch (and cache) the bot's Discord team owner id and role-filtered member ids."""

    only_accept = ("owner", "team", "dev", "master", "admin")
    if who not in only_accept:
        raise ValueError(f"Invalid `who` argument: {who!r}. Must be one of {only_accept!r}.")

    info: AppInfo = await client.application_info()
    team: Team | None = info.team

    if team is None:
        owner_id = info.owner.id
        if who in ("owner", "master"):
            return owner_id, frozenset({owner_id})
        return owner_id, frozenset()

    if who in ("owner", "master"):
        return team.owner_id, frozenset({team.owner_id})
    if who == "admin":
        admins = frozenset(member.id for member in team.members if member.role is TeamMemberRole.admin)
        return team.owner_id, admins
    # "team" / "dev": everyone, since admins are also developers
    return team.owner_id, frozenset(member.id for member in team.members)


@check(name="ALWAYS_FAIL", msg="This operation is impossible!")
async def fail_ward(ctx: Context, *args, **kwargs):
    return False


@check(name="IS_OWNER", msg="You must be a bot owner to use this command!")
async def is_owner(ctx: Context, *args, **kwargs) -> bool:
    if ctx.author.id in get_conf().getintlist("masters", []):
        return True
    owner_id, _ = await get_team_info(ctx.client, "owner")
    return ctx.author.id == owner_id


@check(name="IS_ADMIN", msg="You must be a bot administrator to use this command!", parents=[is_owner])
async def is_admin(ctx: Context, *args, **kwargs):
    old_admin_list: list[int] = get_conf().getintlist("managers", [])
    _, admins = await get_team_info(ctx.client, "admin")
    all_admins: set[int] = set(old_admin_list).union(admins)
    return ctx.author.id in all_admins


@check(name="IS_DEV", msg="You must be a bot developer to use this command!", parents=[is_admin])
async def is_dev(ctx: Context, *args, **kwargs):
    old_team_list: list[int] = get_conf().getintlist("team", [])
    _, team_members = await get_team_info(ctx.client, "team")
    all_team_members: set[int] = set(old_team_list).union(team_members)
    return ctx.author.id in all_team_members


@check(name="IS_REVIEWER", msg="You must be a preamble reviewer to use this command!", parents=[is_dev])
async def is_reviewer(ctx: Context, *args, **kwargs):
    return ctx.author.id in get_conf().getintlist("reviewers", [])


@check(name="IN_GUILD", msg="This command may only be used in a guild.")
async def in_guild(ctx: Context, *args, **kwargs):
    return bool(ctx.msg.guild)


@check(name="GUILD_MODERATOR", msg="This may only be done by a moderator!", requires=[in_guild])
async def guild_moderator(ctx: Context, *args, **kwargs):
    # `requires=[in_guild]` guarantees a Member author
    if not isinstance(ctx.author, Member):
        return False

    has_mod = ctx.author.guild_permissions.administrator
    has_mod = has_mod or ctx.author.guild_permissions.manage_guild

    try:
        modrole = ctx.get_guild_setting.modrole.value
    except KeyError:
        # The `modrole` setting is only registered by Guild_Moderation, which isn't
        # loaded in every deployment -- treat "not registered" as "not configured".
        modrole = None
    return has_mod or (modrole and modrole in ctx.author.roles)


@check(name="GUILD_MANAGER", msg="You need the `manage guild` permission to do this!", requires=[in_guild])
async def guild_manager(ctx: Context, *args, **kwargs):
    return isinstance(ctx.author, Member) and ctx.author.guild_permissions.manage_guild


@check(name="GUILD_ADMIN", msg="You need the `administrator` permission to do this!", requires=[in_guild])
async def guild_admin(ctx: Context, *args, **kwargs):
    return isinstance(ctx.author, Member) and ctx.author.guild_permissions.administrator
