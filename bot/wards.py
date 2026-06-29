from cmdClient import check, Context  # noqa

from config import get_conf


@check(name="ALWAYS_FAIL", msg="This operation is impossible!")
async def fail_ward(ctx: Context, *args, **kwargs):
    return False


@check(name="IS_MASTER", msg="You must be a bot owner to use this command!")
async def is_master(ctx: Context, *args, **kwargs):
    return ctx.author.id in get_conf().getintlist("masters", [])


@check(name="IS_DEV", msg="You must be a bot developer to use this command!", parents=[is_master])
async def is_dev(ctx: Context, *args, **kwargs):
    return ctx.author.id in get_conf().getintlist("developers", [])


@check(name="IS_MANAGER", msg="You must be a bot manager to use this command!", parents=[is_dev])
async def is_manager(ctx: Context, *args, **kwargs):
    return ctx.author.id in get_conf().getintlist("managers", [])


@check(name="IS_REVIEWER", msg="You must be a preamble reviewer to use this command!", parents=[is_manager])
async def is_reviewer(ctx: Context, *args, **kwargs):
    return ctx.author.id in get_conf().getintlist("reviewers", [])


@check(name="IN_GUILD", msg="This command may only be used in a guild.")
async def in_guild(ctx: Context, *args, **kwargs):
    return bool(ctx.msg.guild)


@check(name="GUILD_MODERATOR", msg="This may only be done by a moderator!", requires=[in_guild])
async def guild_moderator(ctx: Context, *args, **kwargs):
    has_mod = ctx.author.guild_permissions.administrator
    has_mod = has_mod or ctx.author.guild_permissions.manage_guild

    modrole = ctx.get_guild_setting.modrole.value
    return has_mod or (modrole and modrole in ctx.author.roles)


@check(name="GUILD_MANAGER", msg="You need the `manage guild` permission to do this!", requires=[in_guild])
async def guild_manager(ctx: Context, *args, **kwargs):
    return ctx.author.guild_permissions.manage_guild


@check(name="GUILD_ADMIN", msg="You need the `administrator` permission to do this!", requires=[in_guild])
async def guild_admin(ctx: Context, *args, **kwargs):
    return ctx.author.guild_permissions.administrator
