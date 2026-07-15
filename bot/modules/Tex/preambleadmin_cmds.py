import asyncio
from contextlib import suppress
from datetime import datetime

import discord
from cmdClient import Context  # noqa
from cmdClient.lib import ResponseTimedOut, UserCancelled
from wards import is_admin, is_reviewer

from .core.LatexGuild import LatexGuild
from .core.preamble_utils import (
    approve_submission,
    confirm,
    deny_submission,
    judgement_reactions,
    preamblelog,
    resolve_pending_preamble,
    set_user_preamble,
    view_preamble,
    view_preamble_diff,
)
from .module import latex_module as module


async def approval_queue(ctx: Context):
    """
    Show a selectable list of preambles to be approved/denied
    """
    # Run the whole thing in a loop, so we keep asking for judgements until there are none left

    while True:
        # Generate the list of users waiting for judgement
        waiting = ctx.client.data.user_pending_preambles.select_where(
            select_columns=("userid", "username", "app", "submission_time", "submission_source_name"),
        )

        # Quit if there is nothing to approve
        if waiting:
            waiting = sorted(waiting, key=lambda waiter: waiter["submission_time"])

            # Make a pretty approval list
            waiting_list = [
                "{} ({}) from '{}' on '{}'".format(
                    waiter["username"],
                    waiter["userid"],
                    waiter["submission_source_name"],
                    waiter["app"],
                )
                for waiter in waiting
            ]

            # Ask the bot manager to select a waiting preamble
            try:
                result = await ctx.selector("Please select a pending preamble to approve/test/deny.", waiting_list)
            except UserCancelled:
                await ctx.reply("Pending preamble selector cancelled.")
                break
            except ResponseTimedOut:
                await ctx.reply("Timed out waiting for a selection.")
                break

            # Display the preamble for judgement
            currently_on_wait = waiting[0][0]
            judging = ctx.client.data.user_pending_preambles.select_where(userid=currently_on_wait)[0]

            current_preamble_row = ctx.client.data.user_latex_preambles.select_where(userid=currently_on_wait)
            current: str | None = current_preamble_row[0]["preamble"] if current_preamble_row else None
            sub_msg = await view_preamble_diff(
                ctx,
                preamble_old=current,
                preamble_pending=judging["pending_preamble"],
                title="Preamble submission!",
                start_page=-1,
                author=waiting_list[result],
                time=datetime.fromtimestamp(float(judging["submission_time"]), tz=datetime.now().astimezone().tzinfo),
                header=judging["submission_summary"],
            )
            # Give a warning, if required, about not being able to see the user
            if judging["app"] != ctx.client.app and ctx.client.get_guild(judging["submission_source_id"]) is None:
                await ctx.reply(
                    "Warning: This user submitted their request from a different app, "
                    "and this shard cannot see the submission guild.\n"
                    "If this client does not share a guild with the user, "
                    "I will not be able to message them.",
                )
            # Add the approval/denial/testing emojis to the submission
            await judgement_reactions(ctx, judging["userid"], sub_msg)
        else:
            return await ctx.reply("All preambles assessed, good work!")

        # Remove the submission message, if possible
        with suppress(discord.NotFound):
            await sub_msg.delete()


async def user_admin(ctx: Context, userid: int):
    """
    Shows a preamble management menu for a single user.
    Menu:
        1. Show current preamble
        2. Set preamble
        3. Reset preamble
        4. Approve/Deny pending preamble (Only appears if user has a pending submission.)
    """
    # Get the data interfaces, for faster access
    preamble_data = ctx.client.data.user_latex_preambles
    pending_preamble_data = ctx.client.data.user_pending_preambles

    # Obtain user's preamble data
    current_preamble_row = preamble_data.select_where(userid=userid)
    current_preamble = current_preamble_row[0] if current_preamble_row else None

    pending_preamble_row = pending_preamble_data.select_where(userid=userid)
    pending_preamble = pending_preamble_row[0] if pending_preamble_row else None

    # Setup the menu options and menu
    menu_items = ["Show current preamble", "Set preamble (manager)", "Reset preamble (manager)"]
    menu_message = f"Preamble management menu for user {userid}"

    # Add the judgement option if there is a pending preamble
    if pending_preamble:
        menu_items.append("Approve/Deny pending preamble")

    # Get the user, if possible
    try:
        user = await ctx.client.fetch_user(userid)
    except discord.NotFound:
        user = None
    except discord.HTTPException:
        user = None

    author = f"{user!s} ({userid})" if user else str(userid)

    # Run the selector and show the menu
    result = await ctx.selector(menu_message, menu_items)

    match result:
        case 0:
            # Show the preamble
            preamble = current_preamble["preamble"]
            if not preamble:
                await ctx.reply("This user doesn't have a custom preamble set!")
            else:
                title = "Current preamble"
                await view_preamble(ctx, preamble, title, author=author, file_react=True)
        case 1:
            # Set the preamble. Takes file input as well as message input.
            # Also asks for confirmation before setting.

            if not await is_admin.run(ctx):
                return await ctx.error_reply("This can only be used by bot managers.")

            # Prompt for new preamble
            prompt = "Please enter or upload the new preamble, or type `c` now to cancel."

            preamble = None
            offer_msg = await ctx.reply(prompt)
            try:
                result_msg = await ctx.client.wait_for(
                    "message",
                    check=lambda msg: msg.author == ctx.author and msg.channel == ctx.ch,
                    timeout=600,
                )
            except asyncio.TimeoutError as toe:
                raise ResponseTimedOut("Timed out waiting for a menu selection.") from toe
            finally:
                await offer_msg.delete()

            # Grab response content, using the contents of the first attachment if it exists
            if result_msg is None or result_msg.content.lower() in ["c", "cancel"]:
                await ctx.error_reply("User menu cancelled.")
            elif result_msg.attachments:
                attachment = result_msg.attachments[0]

                # Check the filesize, over 500KB is not okay
                if attachment.size >= 500000:
                    return await ctx.error_reply("Attached file is too large.")

                try:
                    preamble = str(await attachment.read(), encoding="utf-8", errors="strict")
                except UnicodeError:
                    return await ctx.error_reply(
                        "Couldn't decode the attached file, please ensure it uses the `utf-8` encoding.",
                    )
            else:
                preamble = result_msg.content

            # If out of all that we didn't get a preamble, return
            if preamble is None:
                return None

            # Confirm submission
            prompt = "Please confirm the following preamble modification."
            result = await confirm(ctx, prompt, preamble)
            if not result:
                raise UserCancelled("Modification cancelled.")

            # Finally, set the preamble
            set_user_preamble(
                ctx.client,
                userid,
                preamble=preamble,
                previous_preamble=current_preamble["preamble"] if current_preamble else None,
            )

            await ctx.reply("The user's preamble was updated.")
            await preamblelog(
                ctx,
                "Manual preamble update",
                header=f"{ctx.author} ({ctx.author.id}) manually updated the preamble",
                user=user,
                source=preamble,
            )
        case 2:
            # Reset the current preamble to the default

            if not await is_admin.run(ctx):
                return await ctx.error_reply("This can only be used by bot managers.")

            set_user_preamble(
                ctx.client,
                userid,
                preamble=None,
                previous_preamble=current_preamble["preamble"] if current_preamble else None,
            )

            await resolve_pending_preamble(ctx, userid, "Preamble was reset", colour=discord.Colour.red())
            await ctx.reply("The user's preamble was reset to the default!")

            await preamblelog(
                ctx,
                "Manual preamble reset",
                header=f"{ctx.author} ({ctx.author.id}) manually reset the preamble",
                user=user,
            )
        case 3:
            # Judge the pending preamble
            if not pending_preamble:
                return await ctx.error_reply("This user no longer has a pending preamble!")

            # Display the preamble for judgement
            judging = pending_preamble
            sub_msg = await view_preamble(
                ctx,
                current_preamble,
                judging["pending_preamble"],
                "Preamble submission!",
                start_page=-1,
                author="{} ({})".format(judging["username"], userid),
                time=datetime.fromtimestamp(judging["submission_time"], tz=discord.utils.utcnow().astimezone().tzinfo),
                header=judging["submission_summary"],
            )

            # Give a warning, if required, about not being able to see the user
            if judging["app"] != ctx.client.app and ctx.client.get_guild(judging["submission_source_id"]) is None:
                await ctx.reply(
                    "Warning: This user submitted their request from a different app, "
                    "and this shard cannot see the submission guild.\n"
                    "If this client does not share a guild with the user, "
                    "I will not be able to message them.",
                )

            # Add the approval/denial/testing emojis to the submission
            await judgement_reactions(ctx, judging["userid"], sub_msg)

            # Remove the submission message, if possible
            with suppress(discord.NotFound):
                await sub_msg.delete()
    return None


async def guild_admin(ctx: Context, guildid: int):
    """
    Shows a preamble management menu for a single guild.
    Menu:
        1. Show current preamble
        2. Set preamble
        3. Reset preamble
    """
    if not await is_admin.run(ctx):
        return await ctx.error_reply("This can only be used by bot managers.")
    # Get the data interfaces, for faster access
    preamble_data = ctx.client.data.guild_latex_preambles

    # Obtain guild's preamble data
    current_preamble_row = preamble_data.select_where(guildid=guildid)
    current_preamble = current_preamble_row[0] if current_preamble_row else None

    # Setup the menu options and menu
    menu_items = ["Show current preamble", "Set preamble", "Reset preamble"]
    menu_message = f"Preamble management menu for guild {guildid}"

    # Get the guild, if possible
    try:
        guild = await ctx.client.fetch_guild(guildid)
    except discord.NotFound:
        guild = None
    except discord.Forbidden:
        guild = None
    except discord.HTTPException:
        guild = None

    author = f"{guild!s} ({guildid})" if guild else str(guildid)

    # Run the selector and show the menu
    result = await ctx.selector(menu_message, menu_items)
    match result:
        case 0:
            # Show the preamble
            preamble = current_preamble["preamble"]
            if not preamble:
                await ctx.reply("This guild doesn't have a custom preamble set!")
            else:
                title = "Current guild preamble"
                await view_preamble(ctx, preamble, title, author=author, file_react=True)
        case 1:
            # Set the preamble. Takes file input as well as message input.
            # Also asks for confirmation before setting.

            # Prompt for new preamble
            prompt = "Please enter or upload the new guild preamble, or type `c` now to cancel."

            preamble = None
            offer_msg = await ctx.reply(prompt)
            try:
                result_msg = await ctx.client.wait_for(
                    "message",
                    check=lambda msg: msg.author == ctx.author and msg.channel == ctx.ch,
                    timeout=600,
                )
            except asyncio.TimeoutError as toe:
                raise ResponseTimedOut("Timed out waiting for a menu selection.") from toe
            finally:
                await offer_msg.delete()

            # Grab response content, using the contents of the first attachment if it exists
            if result_msg is None or result_msg.content.lower() in ["c", "cancel"]:
                await ctx.error_reply("Guild menu cancelled.")
            elif result_msg.attachments:
                attachment = result_msg.attachments[0]

                # If the file is over 1MB, it probably isn't a valid preamble.
                if attachment.size >= 1000000:
                    return await ctx.error_reply("Attached file is too large to process (over `1MB`).")

                try:
                    preamble = str(await attachment.read(), encoding="utf-8", errors="strict")
                except UnicodeError:
                    return await ctx.error_reply(
                        "Couldn't decode the attached file, please ensure it uses the `utf-8` codec.",
                    )
            else:
                preamble = result_msg.content

            # If out of all that we didn't get a preamble, return
            if preamble is None:
                return None

            # Confirm submission
            prompt = "Please confirm the following preamble modification."
            result = await confirm(ctx, prompt, preamble)
            if not result:
                raise UserCancelled("Modification cancelled.")

            # Finally, set the preamble
            preamble_data.insert(allow_replace=True, guildid=guildid, preamble=preamble)
            LatexGuild.get(guildid).load()

            await ctx.reply("The guild's preamble was updated.")
            await preamblelog(
                ctx,
                "Manual preamble update",
                header=f"{ctx.author} ({ctx.author.id}) manually updated the preamble",
                user=guild,
                source=preamble,
            )
        case 2:
            # Reset the current preamble to the default
            preamble_data.delete_where(guildid=guildid)
            LatexGuild.get(guildid).load()

            await resolve_pending_preamble(ctx, guildid, "Guild preamble was reset", colour=discord.Colour.red())
            await ctx.reply("The guild's preamble was reset to the default!")

            await preamblelog(
                ctx,
                "Manual guild preamble reset",
                header=f"{ctx.author} ({ctx.author.id}) manually reset the preamble",
                user=guild,
            )
    return None


async def general_menu(ctx):
    await ctx.reply("Not implemented yet!")


@module.cmd(
    "preambleadmin",
    hidden=True,
    desc="Administrate the LaTeX preamble system",
    aliases=["pa"],
    flags=["user==", "guild==", "menu", "approve=", "deny=", "a=", "d=", "r=="],
)
@is_reviewer()
async def cmd_preambleadmin(ctx, flags):
    """
    Usage``:
        {prefix}pa
        {prefix}pa --menu
        {prefix}pa --user <userid>
        {prefix}pa --guild <guildid>
        {prefix}pa (-a | --approve) [userid] [-r <reason>]
        {prefix}pa (-d | --deny) [userid] [-r <reason>]
    Description:
        Manage the preamble system.
        With no arguments, opens the preamble approval queue.
        Several features not fully implemented.
    """
    # Handle user flag
    if flags["user"]:
        await user_admin(ctx, int(flags["user"]))
        return

    # Handle guild flag
    if flags["guild"]:
        await guild_admin(ctx, int(flags["guild"]))
        return

    # Handle menu flag
    if flags["menu"]:
        await general_menu(ctx)
        return

    # Handle raw approvals
    if flags["approve"] or flags["a"]:
        userid = int(flags["approve"] or flags["a"])
        await approve_submission(ctx, userid, ctx.author, reason=flags["r"] or None)
        return

    # Handle raw denials
    if flags["deny"] or flags["d"]:
        userid = int(flags["deny"] or flags["d"])
        await deny_submission(ctx, userid, ctx.author, reason=flags["r"] or None)
        return

    # Handle default action, i.e. showing approval queue
    await approval_queue(ctx)
