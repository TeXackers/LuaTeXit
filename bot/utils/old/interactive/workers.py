import discord


def load_into(bot):
    @bot.util
    async def find_user(ctx, user_str, in_server=False, interactive=False, limit=20, collection=None, is_member=True):
        if user_str == "":
            return None
        maybe_user_id = user_str.strip("<@!> ")
        if is_member:

            def is_user(member):
                return (user_str.lower() in member.display_name.lower()) or (user_str.lower() in str(member).lower())

        else:

            def is_user(member):
                return user_str.lower() in str(member).lower()

        collection = (
            collection if collection is not None else (ctx.server.members if in_server else ctx.bot.get_all_members())
        )
        collection = list(collection)
        if maybe_user_id.isdigit():
            user = discord.utils.get(collection, id=maybe_user_id)
            if user:
                return user
        collection_names = [user.name for user in collection]
        if interactive:
            users = list(filter(is_user, collection))
            if len(users) == 0:
                return None
            if len(users) == 1:
                return users[0]
            if is_member:
                names = [
                    "{} {} {}".format(
                        user.nick if user.nick else (user if collection_names.count(user.name) > 1 else user.name),
                        (f"<{user}>") if user.nick else "",
                        (f"<{user.id}>") if not in_server else "",
                    )
                    for user in users
                ]
            else:
                names = [f"{user} ({user.id})" for user in users]
            selected = await ctx.selector(f"Multiple users found matching `{user_str}`! Please select one.", names)
            if selected is None:
                return None
            return users[selected]
        return discord.utils.find(is_user, collection)

    @bot.util
    async def offer_create_role(ctx, input, timeout=30):
        result = await ctx.ask("Would you like to create this role?", timeout=timeout)
        if result == 0:
            return None
        try:
            # TODO: Lots of fancy stuff, move this out to an interactive create role utility
            role = await ctx.bot.create_role(ctx.server, name=input)
        except discord.Forbidden:
            await ctx.reply("Sorry, it seems I don't have permissions to create a role!")
            return None
        await ctx.reply(f"You have created the role `{input}`!")
        return role

    @bot.util
    async def create_role(ctx, name):
        pass

    @bot.util
    async def find_role(ctx, userstr, create=False, interactive=False, collection=None):
        if not ctx.server:
            ctx.cmd_err = (1, "This is not valid outside of a server!")
            return None
        if userstr == "":
            await ctx.reply("No role name was provided. Please try again.")
            ctx.cmd_err = (-1, "")
            return None

        collection = collection if collection is not None else ctx.server.roles

        roleid = userstr.strip("<#@!>")
        if interactive:

            def check(role):
                return (role.id == roleid) or (userstr.lower() in role.name.lower())

            roles = list(filter(check, collection))
            if len(roles) == 0:
                role = None
            else:
                selected = await ctx.selector(
                    f"Multiple roles found matching `{userstr}`! Please select one.", [role.name for role in roles]
                )
                if selected is None:
                    return None
                role = roles[selected]
        else:
            if roleid.isdigit():

                def is_role(role):
                    return role.id == roleid

            else:

                def is_role(role):
                    return userstr.lower() in role.name.lower()

            role = discord.utils.find(is_role, collection)
        if role:
            return role
        msg = await ctx.reply(f"Couldn't find a role matching `{userstr}`!")
        if create:
            role = await ctx.offer_create_role(userstr)
            if not role:
                ctx.cmd_err = (1, "Aborting...")
                await ctx.bot.delete_message(msg)
                return None
            await ctx.bot.delete_message(msg)
            role = discord.utils.get(ctx.server.roles, id=role.id)
            return role
        return None

    @bot.util
    async def find_channel(ctx, userstr, create=False, interactive=False, collection=None):
        if not ctx.server:
            ctx.cmd_err = (1, "This is not valid outside of a server!")
            return None
        if userstr == "":
            await ctx.reply("No channel name was provided. Please try again.")
            ctx.cmd_err = (-1, "")
            return None

        collection = collection if collection is not None else ctx.server.channels

        channelid = userstr.strip("<#@>")
        tv = {"text": "Text", "voice": "Voice", "4": "Category"}
        if interactive:

            def check(channel):
                return (channel.id == channelid) or (userstr.lower() in channel.name.lower())

            channels = list(filter(check, collection))
            if len(channels) == 0:
                channel = None
            else:
                selected = await ctx.selector(
                    f"Multiple channels found matching `{userstr}`! Please select one.",
                    [f"{channel.name} ({tv[str(channel.type)]})" for channel in channels],
                )
                if selected is None:
                    return None
                channel = channels[selected]
        else:
            if channelid.isdigit():

                def is_channel(channel):
                    return channel.id == channelid

            else:

                def is_channel(channel):
                    return userstr.lower() in channel.name.lower()

            channel = discord.utils.find(is_channel, collection)
        if channel:
            return channel
        await ctx.reply(f"Couldn't find a channel matching `{userstr}`!")
        return None
