import discord
from cmdClient import Context  # noqa
from cmdClient.lib import ResponseTimedOut, SafeCancellation, UserCancelled
from wards import in_guild

from .module import utils_module as module

# Provides giveme


@module.cmd(
    "giveme",
    desc="Request, list, and modify the guild's self assignable roles.",
    aliases=["selfroles", "selfrole", "sroles", "srole", "iam", "iamnot", "roleme"],
    flags=["add", "remove", "list"],
)
@in_guild()
async def cmd_giveme(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}giveme
        {prefix}giveme --list
        {prefix}iam role1, role2, role3
        {prefix}iamnot role1, role2, role3
        {prefix}sroles --add role1, role2, role3
        {prefix}sroles --remove role1, role2, role3
    Description:
        List the self assignable roles in this guild, and assign them or relinquish them.
        The roles may be specified by name, id, or partial name.
        If no roles are given, you will be prompted to choose them from a list.

        The `iamnot` alias will *take* a specified role rather than *give* it.
        The other aliases will prompt for removal if you already have the role.
    Administration:
        If you have the `MANAGE ROLES` and `MANAGE GUILD` permissions,\
        you may set or unset the self assignable roles with the `add` and `remove` flags.
        If possible, when setting I will offer to create any roles which don't exist.

        Guild admins may also setup selfroles via `{prefix}config selfroles`.
    Flags::
        list: List the self-assignable roles in the guild.
        add: Add new self assignable roles (moderator only).
        remove: Remove self assignable roles (moderator only).
    Examples``:
        {prefix}selfrole Homotopy Theory --add
        {prefix}giveme Homotopy
        {prefix}selfrole Homotopy --remove
    """
    # Pre-get the config and the values for this guild
    selfrole_config = ctx.get_guild_setting.selfroles
    selfroles = selfrole_config.value

    # List of roles to show in the role list selector
    select_from = selfroles if not flags["add"] else ctx.guild.roles
    rolestrs = [chars.strip() for chars in ctx.args.split(",")]

    # Remove empty strings
    rolestrs = [rolestr for rolestr in rolestrs if rolestr]

    # My top role with manage_roles
    my_max_role = max(
        (role for role in ctx.guild.me.roles if role.permissions.manage_roles or role.permissions.administrator),
        key=lambda r: r.position,
        default=None,
    )
    if my_max_role is None:
        return await ctx.error_reply("I don't have enough permissions to manage your selfroles!")

    # Handle administration flags
    if flags["add"] or flags["remove"]:
        # Permission resolution, get the highest role position the author may add
        modrole_pos = None
        if ctx.author == ctx.guild.owner:
            modrole_pos = len(ctx.guild.roles)
        elif ctx.author.guild_permissions.manage_guild and ctx.author.guild_permissions.manage_roles:
            modrole_pos = max(
                (role for role in ctx.author.roles if role.permissions.manage_roles or role.permissions.administrator),
                key=lambda r: r.position,
            ).position

        # Handle insufficient permissions
        if modrole_pos is None:
            return await ctx.error_reply(
                "You need to have both the `MANAGE ROLES` and `MANAGE GUILD` permissions to edit guild selfroles!\n"
                "Use again with no flags to update your own roles.",
            )

        if flags["add"] and flags["remove"]:
            return await ctx.error_reply("Do you want me to add selfroles or remove them? One action at a time please!")

        if flags["add"]:
            # Handle adding without arguments
            if not ctx.args:
                return await ctx.error_reply(
                    f"**Usage:** `{await ctx.best_prefix()}{ctx.alias} --add role1, role2, role3`",
                )

            roles = [
                await ctx.find_role(
                    rolestr,
                    interactive=True,
                    collection=select_from,
                    create=True,
                    allow_notfound=False,
                )
                for rolestr in rolestrs
            ]

            # Check these roles
            too_high_roles = [role for role in roles if role.position >= modrole_pos]
            if too_high_roles:
                return await ctx.error_reply(
                    "The following role(s) are equal or above your top role with `manage_role` permissions. "
                    "The guild selfroles were not modified.\n"
                    "`{}`".format("`, `".join(r.name for r in too_high_roles)),
                )

            too_high_for_me_roles = [role for role in roles if role.position >= my_max_role.position]
            if too_high_for_me_roles:
                return await ctx.error_reply(
                    "**Warning:** The following roles are equal or above my top role with the `manage_role` permission."
                    " I will not be able to give them to requesting members!\n"
                    "`{}`".format("`, `".join(r.name for r in too_high_for_me_roles)),
                )

            if any(role is None for role in roles):
                # This shouldn't happen due to the `allow_notfound=False` in `find_role`.
                return None

            # Set roles
            selfrole_config.value = list(set(selfroles + roles))

            return await ctx.reply("The requested selfroles have been added!")
        if flags["remove"]:
            # Check if there's nothing to remove
            if not selfroles:
                return await ctx.error_reply("This guild has no selfroles! Nothing to remove.")

            # If we don't have arguments we will need to select some selfroles
            if not ctx.args:
                try:
                    results = await ctx.multi_selector("Please select the selfroles to remove.", select_from)
                except ResponseTimedOut:
                    raise ResponseTimedOut("Selfrole selector timed out, no roles were removed") from None
                except UserCancelled:
                    raise UserCancelled("Selfrole selector cancelled, no roles were removed.") from None
                roles = [select_from[i] for i in results]
            else:
                roles = [
                    await ctx.find_role(rolestr, interactive=True, collection=select_from, allow_notfound=False)
                    for rolestr in rolestrs
                ]

            # Remove the selfroles
            selfrole_config.value = [role for role in selfroles if role not in roles]
            return await ctx.reply("The requested selfroles have been removed.")
    # End of administrator mode handling

    # Handle list flag
    if flags["list"]:
        if selfroles:
            role_list = "```css\n{}\n```".format(", ".join([role.name for role in selfroles]))
            msg = (
                "**Self assignable roles for this guild**:\n"
                f"{role_list}"
                f"Use `{await ctx.best_prefix()}iam role1, role2, ...` to assign yourself roles.\n"
                f"Use `{await ctx.best_prefix()}iamnot role1, role2, ...` to remove the roles."
            )
        else:
            msg = (
                "No self assignable roles have been set for this guild. "
                f"See `{await ctx.best_prefix()}help selfroles` for more information about creating selfroles."
            )

        return await ctx.reply(msg)

    # All flags have been handled, now check the alias and parse or request user input
    add_alias = ctx.alias.lower() != "iamnot"

    if ctx.args:
        # Parse arguments
        roles = []
        for rolestr in rolestrs:
            try:
                role = await ctx.find_role(rolestr, interactive=True, collection=select_from, allow_notfound=False)
            except SafeCancellation:
                return await ctx.error_reply(
                    f"No selfroles matching `{rolestr}`.\nSee `{await ctx.best_prefix()}selfroles --list` for the list of valid selfroles.",
                )

            roles.append(role)
        if add_alias:
            remove_roles = [role for role in roles if role in ctx.author.roles]
            if remove_roles:
                resp = await ctx.ask(
                    "You already have the selfroles `{}`, do you want to remove them? (`y(es)`/`n(o)`)\n"
                    "(Tip: use `{}iamnot` to remove roles without this prompt.)".format(
                        "`, `".join(r.name for r in remove_roles),
                        await ctx.best_prefix(),
                    ),
                    add_hints=False,
                )
                if not resp:
                    roles = [role for role in roles if role not in remove_roles]
        else:
            add_roles = [role for role in roles if role not in ctx.author.roles]
            if add_roles:
                resp = await ctx.ask(
                    "You don't have the selfroles `{}`, do you want to add them? (`y(es)`/`n(o)`)\n"
                    "(Tip: use `{}iam` to add roles without this prompt.)".format(
                        "`, `".join(r.name for r in add_roles),
                        await ctx.best_prefix(),
                    ),
                    add_hints=False,
                )
                if not resp:
                    roles = [role for role in roles if role not in add_roles]
    elif len(selfroles) == 1:
        # Special case for a single selfrole, allow any alias to toggle it
        roles = selfroles
    else:
        # Case for empty arguments
        if add_alias:
            offer_str = f"Please select the desired selfroles! (Use `{await ctx.best_prefix()}iamnot` to remove your current selfroles.)"
            select_from = [role for role in selfroles if role not in ctx.author.roles]
            if not select_from:
                return await ctx.error_reply(
                    f"You have all the selfroles! (Use `{await ctx.best_prefix()}iamnot` to remove them).",
                )
        else:
            offer_str = "Please select the selfroles to remove."
            select_from = [role for role in selfroles if role in ctx.author.roles]
            if not select_from:
                return await ctx.error_reply(
                    f"You don't have any selfroles! Use `{await ctx.best_prefix()}iam` to get some.",
                )

        # Request roles to toggle
        try:
            results = await ctx.multi_selector(offer_str, select_from, allow_single=True)
        except ResponseTimedOut:
            raise ResponseTimedOut("Selfrole selector timed out, your roles were not updated.") from None
        except UserCancelled:
            raise UserCancelled("Selfrole selector cancelled, your roles were not updated.") from None

        roles = [select_from[i] for i in results]

    # We have parsed the user input, and harassed the user where required.
    # We now have a list of selfroles to toggle for the user.

    # Make sure this list isn't empty
    if not roles:
        return await ctx.error_reply("No roles to add or remove, nothing to do.")

    # Make sure the roles are unique
    roles = list(set(roles))

    # Check if we can't handle any of the roles, remove them for later processing and error handling
    too_high_for_me = [role for role in roles if role >= my_max_role]
    if too_high_for_me:
        roles = [role for role in roles if role not in too_high_for_me]

    # Break the roles up into roles to remove and roles to add
    roles_to_remove = [role for role in roles if role in ctx.author.roles]
    roles_to_add = [role for role in roles if role not in ctx.author.roles]

    # Storing actual state for the final report message
    actually_removed = None
    actually_added = None
    perm_failed = []
    unknown_failed = []

    # Handle adding roles
    if roles_to_add:
        try:
            await ctx.author.add_roles(*roles_to_add, reason="User requested selfroles.")
            actually_added = roles_to_add
        except discord.Forbidden:
            perm_failed += roles_to_add
        except discord.HTTPException:
            unknown_failed += roles_to_add

    # Handle removing roles
    if roles_to_remove:
        try:
            await ctx.author.remove_roles(*roles_to_remove, reason="User requested selfrole removal.")
            actually_removed = roles_to_remove
        except discord.Forbidden:
            perm_failed += roles_to_remove
        except discord.HTTPException:
            unknown_failed += roles_to_remove

    # Final report
    msg_components = []
    if actually_added:
        if len(actually_added) == 1:
            msg_components.append(f"Gave you the `{actually_added[0].name}` selfrole.")
        else:
            msg_components.append(
                "Gave you the following selfroles: `{}`".format("`, `".join(r.name for r in actually_added)),
            )

    if actually_removed:
        if len(actually_removed) == 1:
            msg_components.append(f"Removed the `{actually_removed[0].name}` role from you.")
        else:
            msg_components.append(
                "Removed the following selfroles from you: `{}`".format("`, `".join(r.name for r in actually_removed)),
            )

    if perm_failed:
        msg_components.append(
            "Lacking permissions! The following selfroles were ignored: `{}".format(
                "`, `".join(r.name for r in perm_failed),
            ),
        )

    if unknown_failed:
        msg_components.append(
            "Unknown error!! The following selfroles were ignored: `{}".format(
                "`, `".join(r.name for r in unknown_failed),
            ),
        )

    if too_high_for_me:
        msg_components.append(
            "I lacked permissions to modify the following roles for you: `{}`".format(
                "`, `".join(r.name for r in too_high_for_me),
            ),
        )

    return await ctx.reply("\n".join(msg_components))
