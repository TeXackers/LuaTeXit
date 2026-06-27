import discord
from ModEvent import ModEvent


def load_into(bot):
    @bot.util
    async def request_reason(ctx, action="ban"):
        reason = await ctx.input(f"📋 Please provide a reason! (`no` for no reason or `c` to abort {action})")
        if not reason:
            await ctx.reply("📋 Request timed out, aborting.")
            return None
        if reason.lower() == "no":
            reason = "None"
        elif reason.lower() == "c":
            await ctx.reply("📋 Aborting...")
            return None
        return reason


async def role_finder(ctx, user_str, msg):
    role = await ctx.find_role(user_str, interactive=True, create=True)
    if role is None:
        if ctx.cmd_err[0] != -1:
            msg = msg + f"\t🚨 Couldn't find role `{user_str}`, skipping\n"
        else:
            msg = msg + f"\t🗑 Role selection aborted for `{user_str}`, skipping\n"
            ctx.cmd_err = (0, "")
    elif role >= ctx.author.top_role:
        msg = msg + "\t🚨 Role is above your highest role, skipping\n"
        role = None
    return (role, msg)


async def member_finder(ctx, user_str, msg, hack=False, collection=None, is_member=True):
    if hack:
        if user_str.isdigit():
            try:
                print(user_str)
                member_info = await ctx.bot.get_user_info(user_str.strip())
            except discord.NotFound:
                msg += f"\t🚨 User with id `{user_str}` does not exist, skipping\n"
                return (None, msg)
            member = discord.Object(id=user_str)
            member.server = ctx.server
            member.name = member_info.name
            member.__str__ = member_info.__str__
            return (member, msg)
    user = await ctx.find_user(user_str, in_server=True, interactive=True, collection=collection, is_member=is_member)
    if user is None:
        if ctx.cmd_err[0] != -1:
            msg = msg + f"\t🚨 Couldn't find user `{user_str}`, skipping\n"
        else:
            msg = msg + f"\t🗑 User selection aborted for `{user_str}`, skipping\n"
            ctx.cmd_err = (0, "")
    return (user, msg)


async def user_finder(ctx, user_str, msg):
    user, msg = await member_finder(ctx, user_str, msg, hack=True)
    return (user, msg)


async def ban_finder(ctx, user_str, msg):
    user, msg = await member_finder(ctx, user_str, msg, collection=await ctx.bot.get_bans(ctx.server), is_member=False)
    return (user, msg)


async def test_action(ctx, user, **kwargs):
    return 0


async def role_result(ctx, result, msg, role, **kwargs):
    if result == 0:
        msg += f"\tAdded role `{role}`."
    elif result == 1:
        msg += f"\tInsufficient permissions to add role `{role}`."
    else:
        msg += f"\tUnknown error while adding role `{role}`, aborting sequence."
        return (1, msg)
    return (0, msg)


async def mod_result(ctx, result, msg, user, **kwargs):
    strings = kwargs["strings"]
    if result in strings["results"]:
        msg += "\t{}".format(strings["results"][result].format(user=user))
        if result >= 0:
            return (0, msg)
        if result < 0:
            return (1, msg)
    else:
        msg += "\t{}".format(strings["fail_unknown"].format(user=user))
        return (1, msg)


async def multi_action(ctx, user_strs, action, finder, result_func, start_str, **kwargs):
    founds = []
    msg = start_str
    out_msg = await ctx.reply(msg)

    for user_str in user_strs:
        if user_str == "":
            continue
        old_msg = msg
        msg += f"\t{user_str}"

        # Attempt to edit message with new string, or repost
        try:
            await ctx.bot.edit_message(out_msg, msg)
        except discord.NotFound:
            out_msg = await ctx.reply(msg)
        found, msg = await finder(ctx, user_str, old_msg)
        if found is None:
            continue
        result = await action(ctx, found, **kwargs)
        code, msg = await result_func(ctx, result, old_msg, found, **kwargs)
        if code:
            break
        if result == 0:
            founds.append(found)
        msg += "\n"

    # Attempt to edit message with final string, or repost
    try:
        await ctx.bot.edit_message(out_msg, msg)
    except discord.NotFound:
        out_msg = await ctx.reply(msg)
    return founds


async def multi_mod_action(ctx, user_strs, action, strings, reason, finder=member_finder, **kwargs):
    users = await multi_action(
        ctx, user_strs, action, finder, mod_result, strings["start"], strings=strings, reason=reason, **kwargs
    )
    if len(users) == 0:
        return
    action = strings["action_name"] if len(users) == 1 else strings["action_multi_name"]
    mod_event = ModEvent(ctx, action, ctx.author, users, reason, timeout=kwargs.get("duration"))
    result = await mod_event.modlog_post()
    if result == 1:
        await ctx.reply(
            "I tried to post to the modlog, but lack the permissions."
        )  # TODO: Offer to repost after modlog works.
    elif result == 2:
        await ctx.reply("I can't access the set modlog channel.")
    elif result == 3:
        await ctx.reply("An unexpected error occurred while trying to post to the modlog.")


async def mod_parse(ctx, multi=True, purge=True, purge_default="0"):
    reason = ""
    if multi:
        users = [user.strip() for user in ctx.arg_str.split(",")]
        reason = ctx.flags["r"]
    reason = reason if reason else (await ctx.request_reason(action=ctx.cmd.name))
    if not reason:
        return (None, None, None) if purge else (None, None)
    if purge:
        purge_days = ctx.flags["p"]
        if not purge_days:
            purge_days = purge_default
        if not purge_days.isdigit():
            await ctx.reply("🚨 Number of days to purge must be a number.")
            return (None, None, None) if purge else (None, None)
        if int(purge_days) > 7:
            await ctx.reply("🚨 Number of days to purge must be less than 7.")
            return (None, None, None) if purge else (None, None)
    return (reason, users, purge_days) if purge else (reason, users)
