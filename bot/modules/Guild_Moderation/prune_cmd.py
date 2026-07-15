import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

import discord
from cmdClient import Context  # noqa
from cmdClient.lib import ResponseTimedOut, UserCancelled
from wards import guild_moderator

from .module import guild_moderation_module as module


BULK_DELETE_MAX_AGE = timedelta(days=14)
SINGLE_DELETE_DELAY = 1.0
BULK_DELETE_DELAY = 1.0
PROGRESS_WARN_TIMEOUT = 300
_active_purges: set[int] = set()


class PruneTarget(NamedTuple):
    """
    A lightweight stand-in for a Message, holding just enough to delete it
    later without keeping the full Message (embeds, attachments, etc.) alive
    in memory for the (potentially long) confirmation wait and delete pass.
    """

    id: int
    created_at: datetime


def _log_purge_result(ctx, channel, count, task):
    """
    Done-callback for a backgrounded purge task: log the outcome instead of
    trying to keep live-updating a progress message no one may still be
    watching.
    """
    label = f"#{channel.name} ({channel.id})"
    try:
        task.result()
    except discord.Forbidden:
        ctx.client.log(
            f"Purge of {count} messages in {label} failed: insufficient permissions.",
            context=f"PRUNE {ctx.msg.id}",
            level=logging.ERROR,
        )
    except discord.HTTPException as e:
        ctx.client.log(
            f"Purge of {count} messages in {label} failed: {e}",
            context=f"PRUNE {ctx.msg.id}",
            level=logging.ERROR,
        )
    else:
        ctx.client.log(f"Purge of {count} messages in {label} completed.", context=f"PRUNE {ctx.msg.id}")


async def _paced_purge(channel, targets, *, reason=None):
    """
    Delete the given messages (by id), bulk-deleting recent ones in batches
    of 100 and individually deleting older ones at a deliberate pace, so
    that a large purge completes reliably instead of hammering the rate
    limit. Messages older than 14 days can't be bulk-deleted at all, so
    those are only ever queried by id and deleted one at a time.
    """
    cutoff = datetime.now(timezone.utc) - BULK_DELETE_MAX_AGE
    bulk_targets = [t for t in targets if t.created_at > cutoff]
    single_targets = [t for t in targets if t.created_at <= cutoff]

    for i in range(0, len(bulk_targets), 100):
        chunk = bulk_targets[i : i + 100]
        await channel.delete_messages(chunk, reason=reason)
        if i + 100 < len(bulk_targets):
            await asyncio.sleep(BULK_DELETE_DELAY)

    for target in single_targets:
        with suppress(discord.NotFound):
            await channel.get_partial_message(target.id).delete()
        await asyncio.sleep(SINGLE_DELETE_DELAY)


@module.cmd(
    "prune",
    desc="Purges messages matching selected criteria from the current channel.",
    aliases=["purge"],
    flags=["r==", "bot", "bots", "user", "embed", "file", "me", "from==", "after==", "before==", "ch==", "force"],
)
@guild_moderator()
async def cmd_prune(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}prune [number] [flags] [--after <msgid>] [--before <YYYY-MM-DD>] [--from <user>] [--ch <channel>] [-r <reason>]
    Description:
        Deletes your command message and messages from the given number of messages before that.
        If neither the number nor `after` is given, deletes from the last 100 messages.

        The flags restrict what types of messages are deleted from this collection.
        If there are multiple flags, only messages matching all the criteria will be deleted.

        To use this command, you need to be a **guild moderator**.\
            That is, you need to have the `manage_guild` permission or the configured `modrole`.

        **Note:** The modlog feature is currently temporarily disabled, so purges will not appear\
            in the modlog until it is reactivated (in the next release).
    Behavioural flags::
        r: Reason for the message purge.
        force: Force a prune without asking for a reason or confirmation.
    Restriction flags::
        bot: Only messages from bots.
        user:  Only messages from non-bots.
        embed:  Only messages with embeds (including link previews).
        file: Only messages with uploaded attachements (e.g. images).
        me: Only messages from me ({ctx.client.user.mention}).
        from: Only messages from the given user (interactive lookup).
        after: Only messages after (not including) the given message id (must be in the last `1000` messages).
        before: Only messages sent before the given date, in `YYYY-MM-DD` format (UTC).
        ch: Purge the given channel instead of the current one (interactive lookup).
    Examples``:
        {prefix}prune 100 --file
        {prefix}prune --after {ctx.msg.id}
        {prefix}prune 10 --me --embed
        {prefix}prune 10 --from {ctx.author.name} --image --force
        {prefix}prune 500 --before 2026-06-01
        {prefix}prune 100 --ch general
    """
    # TODO: --role? Maybe?
    # TODO: find_user won't work for users not in the server. Construct a collection based on message list.

    # Get the target channel from the flag, if provided; otherwise use the current channel
    target_channel = ctx.ch
    if flags["ch"]:
        if flags["ch"] is True:
            return await ctx.error_reply(f"**Usage:** {await ctx.best_prefix()}purge ... --ch <channel> ...")
        found_channel = await ctx.find_channel(flags["ch"], interactive=True, chan_type=discord.ChannelType.text)
        if found_channel is None:
            return None
        target_channel = found_channel

    # First check that we have the permissions we need in the channel
    perms = target_channel.permissions_for(ctx.guild.me)
    if not perms.manage_messages or not perms.read_message_history:
        return await ctx.error_reply(
            f"I lack the `MANAGE MESSAGES` and `READ MESSAGE HISTORY` permissions I require to purge {target_channel.mention}.",
        )

    if target_channel.id in _active_purges:
        return await ctx.error_reply(
            f"A purge is already in progress in {target_channel.mention}. "
            "Please wait for it to finish before starting another.",
        )

    # Get the after message id from the flag, if provided
    after_msg_id = None
    if flags["after"]:
        if flags["after"] is True or not flags["after"].isdigit():
            return await ctx.error_reply(f"**Usage:** {await ctx.best_prefix()}purge ... --after <msgid> ...")

        after_msg_id = int(flags["after"])

    # Get the before date from the flag, if provided
    before_dt = None
    if flags["before"]:
        if flags["before"] is True:
            return await ctx.error_reply(f"**Usage:** {await ctx.best_prefix()}purge ... --before <YYYY-MM-DD> ...")
        try:
            before_dt = datetime.strptime(flags["before"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return await ctx.error_reply(
                f"Couldn't parse `{flags['before']}` as a date. Please use `YYYY-MM-DD` format.",
            )

    # Get the maximum number of messages to search
    if not ctx.args:
        number = 1000 if after_msg_id is not None else 100
    elif not ctx.args.isdigit():
        await ctx.reply("Please give me a valid number of messages to delete. See the help for this command for usage.")
        return None
    else:
        number = int(ctx.args)

    # Retrieve the user from the flag if provided
    user = None
    if flags["from"]:
        user = await ctx.find_member(flags["from"], interactive=True)
        if user is None:
            return await ctx.error_reply("Couldn't find the requested user, cancelling purge.")

    # Retrieve the reason from the flag, or request it
    if flags["r"] is True or not flags["r"]:
        if flags["force"]:
            reason = "None, forced prune."
        else:
            try:
                reason = await ctx.on_input("Please enter a reason for this purge, or `c` to cancel.")
            except ResponseTimedOut:
                raise ResponseTimedOut("Reason prompt timed out, cancelling purge.") from None
            if reason.lower() == "c":
                raise UserCancelled("Moderator cancelled the reason prompt, cancelling purge.")

            if not reason:
                return await ctx.error_reply("No reason provided, cancelling purge.")
    else:
        reason = flags["r"]

    # Attempt to delete the sending message to ensure we have some permissions
    try:
        await ctx.msg.delete()
    except discord.NotFound:
        pass
    except discord.Forbidden as e:
        return await ctx.traceback(
            f"I do not have permissions to delete messages here.\n"
            "If this is in error, please give me the `MANAGE MESSAGES` permission.", f"{e}"
        )

    # Start going through the channel history, counting messages
    count_dict = {"bots": {}, "users": {}}
    message_list = []
    msg_found = False

    async for message in target_channel.history(limit=number, before=before_dt):
        if message.id == after_msg_id:
            msg_found = True
            break

        # Check whether we should delete this message
        to_delete = True
        to_delete = to_delete and (not (flags["bot"] or flags["bots"]) or message.author.bot)
        to_delete = to_delete and (not flags["user"] or not message.author.bot)
        to_delete = to_delete and (not flags["embed"] or message.embeds)
        to_delete = to_delete and (not flags["file"] or message.attachments)
        to_delete = to_delete and (not flags["from"] or message.author == user)
        to_delete = to_delete and (not flags["me"] or message.author == ctx.client.user)

        if to_delete:
            message_list.append(PruneTarget(message.id, message.created_at))
            listing = count_dict["bots" if message.author.bot else "users"]
            if message.author.id not in listing:
                listing[message.author.id] = {"count": 0, "name": f"{message.author}"}
            listing[message.author.id]["count"] += 1

    if after_msg_id and not msg_found:
        return await ctx.reply(f"The given message wasn't found in the last {number} messages")

    if not message_list:
        return await ctx.error_reply("No messages matching the given criteria were found!")

    bot_lines = "\n".join(
        [
            "\t**{name}** ({key}): ***{count}*** messages".format(**count_dict["bots"][key], key=key)
            for key in count_dict["bots"]
        ],
    )
    user_lines = "\n".join(
        [
            "\t**{name}** ({key}): ***{count}*** messages".format(**count_dict["users"][key], key=key)
            for key in count_dict["users"]
        ],
    )
    bot_counts = f"__**Bots**__\n{bot_lines}" if bot_lines else ""
    user_counts = f"__**Users**__\n{user_lines}" if user_lines else ""
    counts = f"{bot_counts}\n{user_counts}"
    abort = False
    if not flags["force"]:
        out_msg = await ctx.reply(
            f"Purging **{len(message_list)}** messages in {target_channel.mention}. Message Breakdown:\n"
            f"{counts}\n--------------------\n"
            "Please type `confirm` to delete the above messages or `abort` to abort now.",
        )
        try:
            reply_msg = await ctx.listen_for(allowed_input=["abort", "confirm"], timeout=60)
        except ResponseTimedOut:
            await ctx.error_reply("Purge confirmation request timed out, cancelling purge.")
            abort = True
        else:
            if reply_msg.content.lower() == "abort":
                await ctx.error_reply("Moderator cancelled message purge.")
                abort = True
        finally:
            with suppress(Exception):
                await out_msg.delete()

    if not abort:
        loading_emoji = ctx.client.conf.emojis.getemoji("loading")
        progress_msg = await ctx.reply(
            f"Purging **{len(message_list)}** messages in {target_channel.mention}, please wait... {loading_emoji}\n\n-# Initiated: {discord.utils.format_dt(discord.utils.utcnow(), 'R')}",
        )
        _active_purges.add(target_channel.id)
        purge_task = asyncio.ensure_future(_paced_purge(target_channel, message_list, reason=reason))
        purge_task.add_done_callback(lambda task: _active_purges.discard(target_channel.id))
        done, _pending = await asyncio.wait({purge_task}, timeout=PROGRESS_WARN_TIMEOUT)

        if purge_task not in done:
            # Taking a while; stop blocking on it here and let it finish in the background, logging the outcome instead
            await progress_msg.edit(
                content=f"Purge of **{len(message_list)}** messages in {target_channel.mention} is taking longer "
                "than 5 minutes, see logs for completion.",
            )
            purge_task.add_done_callback(
                lambda task: _log_purge_result(ctx, target_channel, len(message_list), task),
            )
            return None

        try:
            purge_task.result()
        except discord.Forbidden:
            await progress_msg.edit(content="I have insufficient permissions to delete these messages.")
            abort = True
        except discord.HTTPException:
            await progress_msg.edit(content="An error occurred while purging messages; the purge may be incomplete.")
            abort = True
        else:
            await progress_msg.edit(content="Purge complete.")
    if abort:
        return None

    try:
        await asyncio.sleep(3)
        await progress_msg.delete()
    except Exception:
        pass
