import re
from pathlib import Path

import discord
from cmdClient import Context, cmdClient  # noqa
from cmdClient.lib import ResponseTimedOut
from utils.lib import substitute_ranges

from .core.LatexGuild import LatexGuild
from .core.preamble_utils import (
    confirm,
    preamblelog,
    resolve_pending_preamble,
    submit_preamble,
    view_preamble,
    view_preamble_v2,
)
from .module import latex_module as module
from .resources import default_preamble

__location__: str = str(Path(__file__).resolve().parent)


@module.cmd(
    "preamble",
    desc="View or modify your LaTeX preamble.",
    flags=["reset", "retract", "add", "remove", "revert", "replace"],
)
async def cmd_preamble(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}preamble
        {prefix}preamble --revert
        {prefix}preamble --retract
        {prefix}preamble --reset
        {prefix}preamble --preset [presetname]
        {prefix}preamble --replace [code]
        {prefix}preamble --add [code]
        {prefix}preamble --remove [code]
    Description:
        With no arguments or flags, displays the preamble used to compile your LaTeX.
        The flags may be used to modify or replace your preamble.
        This command supports file uploads, the contents of which are treated as [code].

        If [code] is provided without a flag, it is added to your preamble.
        Note that most preamble modifications must be reviewed by a bot manager.
    Flags::
        add: Add `code` to your preamble, or prompt for new lines to add.
        retract: Retract a previously submitted preamble.
        revert: Switch to your previous preamble
        reset:  Resets your preamble to the default.
        preset: ~~Replace your preamble with one of our pre-built presets~~ (disabled)
        replace: Replaces your preamble with [code], or prompt for the new preamble.
        remove: Removes all lines from your preamble containing the given text, or prompt for line numbers to remove.
    """
    # Get the data interfaces, for faster access
    preamble_data = ctx.client.data.user_latex_preambles
    pending_preamble_data = ctx.client.data.user_pending_preambles

    # Obtain user's preamble data
    current_preamble_row = preamble_data.select_where(userid=ctx.author.id)
    current_preamble = current_preamble_row[0] if current_preamble_row else None

    pending_preamble_row = pending_preamble_data.select_where(userid=ctx.author.id)
    pending_preamble = pending_preamble_row[0] if pending_preamble_row else None

    # Get the effective preamble and the viewing header
    if current_preamble and current_preamble["preamble"]:
        (preamble := current_preamble["preamble"])
        (header := "custom")
    elif ctx.guild and LatexGuild.get(ctx.guild.id).preamble:
        (preamble := LatexGuild.get(ctx.guild.id).preamble)
        (header := "server")
    else:
        (preamble := default_preamble)
        (header := "default")
    # Get the preamble presets
    # presets = []

    # Get the whitelisted packages
    # in resources/whitelisted_packages.txt
    whitelist_file_loc = Path(__location__) / "resources" / "whitelist.txt"
    with whitelist_file_loc.open() as f:
        whitelisted_packages = [line.strip() for line in f]

    # Handle resetting the preamble
    if flags["reset"]:
        # Handle not having a preamble
        if not current_preamble or not current_preamble["preamble"]:
            return await ctx.reply("You don't have a custom user preamble to reset!")

        # Ask the user if they are sure, handling timeout and negative response
        try:
            resp = await ctx.ask("Are you sure you want to reset your preamble to the default?", timeout=60)
        except ResponseTimedOut:
            return await ctx.error_reply(
                "Preamble preset timed out waiting for a response, your preamble was not modified.",
            )
        if not resp:
            return await ctx.error_reply("Cancelling preamble reset, your preamble was not modified.")

        # Now reset the preamble
        preamble_data.insert(
            allow_replace=True,
            userid=ctx.author.id,
            preamble=None,
            previous_preamble=current_preamble["preamble"],
        )

        # Logging
        await preamblelog(ctx, "Preamble has been reset to the default")

        # Notify the user, notifying them about their pending preamble if required
        response = "Your preamble has been reset to the default! Use `{prefix}preamble --revert` to restore it."
        if pending_preamble and not flags["retract"]:
            response += "\nUse `{prefix}preamble --retract` to also retract your pending preamble request"

        await ctx.reply(response.format(prefix=await ctx.best_prefix()))

    # Handle retracting a preamble request
    if flags["retract"]:
        if not pending_preamble:
            return await ctx.error_reply("You don't have a pending preamble request to retract!")

        pending_preamble_data.delete_where(userid=ctx.author.id)

        await resolve_pending_preamble(ctx, ctx.author.id, "Request retracted", colour=discord.Colour.red())
        await preamblelog(ctx, "Preamble request was retracted")

        await ctx.reply("Your pending preamble request has been retracted!")

    if flags["reset"] or flags["retract"]:
        # Return if we have handled these flags
        return None

    # Handle reverting to the previous version of the preamble
    if flags["revert"]:
        # Handle not having a previous preamble
        if not current_preamble or not current_preamble["previous_preamble"]:
            return await ctx.error_reply("No previous preamble to revert to!")

        # Ask for confirmation, handle timeout and negative response
        try:
            resp = await ctx.ask("Are you sure you want to revert your preamble to the previous version?", timeout=60)
        except ResponseTimedOut:
            return await ctx.error_reply(
                "Preamble revert timed out waiting for a response, your preamble was not modified.",
            )
        if not resp:
            return await ctx.error_reply("Cancelling preamble revert, your preamble was not modified.")

        # Revert the preamble
        preamble_data.insert(
            allow_replace=True,
            userid=ctx.author.id,
            preamble=current_preamble["previous_preamble"],
            previous_preamble=current_preamble["preamble"],
        )

        # Logging
        await preamblelog(ctx, "Preamble has been reverted.")
        await ctx.reply(
            f"Your preamble has been reverted to the previous version. Use `{await ctx.best_prefix()}preamble --revert` again to undo.",
        )
        return None

    # Get any input, including the contents of any attached files if they exist
    if ctx.msg.attachments:
        attachment = ctx.msg.attachments[0]

        # If the file is over 1MB, it probably isn't a valid preamble.
        if attachment.size >= 1000000:
            return await ctx.error_reply("Attached file is too large to process (over `1MB`).")

        try:
            args = str(await attachment.read(), encoding="utf-8", errors="strict")
        except UnicodeError:
            return await ctx.error_reply("Couldn't decode the attached file, please ensure it uses the `utf-8` codec.")
    else:
        args = ctx.args

    # Strip args, then remove any codeblock characters
    args = args.strip()
    args = re.sub("(```)(tex|latex)*", "", args, flags=re.IGNORECASE)

    # Handle a request to remove material from the preamble
    if flags["remove"]:
        to_remove = []  # List of line indicies to remove
        new_preamble = None
        lines = preamble.splitlines()

        # If arguments were given, search the current preamble for this string
        if args:
            if args not in preamble:
                return await ctx.error_reply("The requested text doesn't appear in your preamble! Nothing to remove.")
            if "\n" in args:
                # If the requested string has multiple lines and appears, just remove all of them
                new_preamble = preamble.replace(args, "")
            else:
                # Otherwise, make a list of matching lines to remove
                to_remove = [i for i, line in enumerate(lines) if args in line]
        else:
            # If we aren't given anything to remove, prompt the user for which lines they want to remove
            # Generate a version of the current preamble with line numbers
            lined_preamble = "\n".join((f"{i + 1:>2}. {line}" for i, line in enumerate(lines)))

            # Show this to the user and prompt them
            prompt = (
                "Please enter the line numbers and ranges to remove, "
                "separated by commas, or type `c` now to cancel.\n"
                "(Example input: `1, 2-5, 10-20`)"
            )
            prompt_msg = await view_preamble(ctx, lined_preamble, prompt)

            # Handle timeouts and negative response
            try:
                response = await ctx.on_input(prompt_msg)
            except ResponseTimedOut:
                return await ctx.error_reply("Prompt timed out. Your preamble was not updated.")
            if response.lower() == "c":
                return await ctx.error_reply("Preamble modification cancelled. Your preamble was not updated.")

            # Parse provided selection
            parse_failure = False

            # First sanity check input
            if not all((char.isdigit() or not char.strip() or char in ("-", ",")) for char in response):
                parse_failure = True

            # Replace ranges
            try:
                response = substitute_ranges(response)
            except ValueError:
                parse_failure = True

            # Extract numbers
            nums = [num.strip() for num in response.split(",")]
            if not all(num.isdigit() for num in nums):
                parse_failure = True

            # Handle unspecified parsing failure along the way
            if parse_failure:
                return await ctx.error_reply(
                    "Couldn't parse your selection!\n"
                    "Please enter numbers and ranges of numbers separated by commas, e.g. "
                    "`1, 2-5, 10-20`.",
                )

            # Calculate line indicies
            nums = [int(num) - 1 for num in nums]
            if not all(0 <= num < len(lines) for num in nums):
                return await ctx.error_reply(
                    "Couldn't remove requested lines, your selection goes outside of your preamble!",
                )

            # Remove duplicates and set the list of line indices to remove
            to_remove = list(set(nums))

        # Prompt the user and remove the requested lines
        if to_remove:
            for_removal = "\n".join([lines[i] for i in to_remove])
            prompt = "Are you sure you want to remove the following lines from your preamble?"
            try:
                result = await confirm(
                    ctx,
                    prompt,
                    for_removal,
                    footer="Reply with y/n to confirm your preamble request.",
                )
            except ResponseTimedOut:
                return await ctx.error_reply("Prompt timed out, your preamble was not modified.")
            if not result:
                return await ctx.error_reply("Cancelled preamble modification, your preamble was not modified.")

            new_preamble = "\n".join([line for i, line in enumerate(lines) if i not in to_remove])

        # Finally save the new preamble
        if new_preamble is not None:
            preamble_data.insert(
                allow_replace=True,
                userid=ctx.author.id,
                preamble=new_preamble,
                previous_preamble=preamble,
            )
            await ctx.reply("Your preamble has been updated!")
            await preamblelog(ctx, "Material was removed from the preamble. New preamble below.", source=new_preamble)
        return None

    # At this point, the user wants to view, replace, or add to their preamble.

    # Handle a request to replace the preamble
    if flags["replace"]:
        if not args:
            # Prompt the user for the new preamble, handle cancellations and timeout
            prompt = (
                "Please enter your new preamble, or `c` to cancel.\n"
                "**If you wish to upload a file as your preamble, "
                "cancel now and rerun with the file attached.**"
            )
            try:
                new_submission = await ctx.on_input(prompt, timeout=600)
            except ResponseTimedOut:
                return await ctx.error_reply("Query timed out, your preamble was not modified.")
            if new_submission.lower() == "c":
                return await ctx.error_reply("Preamble replacement cancelled, your preamble was not modified.")
        else:
            new_submission = args

        # Remove codeblock characters from submission
        new_submission = re.sub("(```)(tex|latex)*", "", new_submission, flags=re.IGNORECASE)

        # Confirm submission
        prompt = "Please confirm you want to replace your preamble with the following."
        try:
            result = await confirm(
                ctx,
                prompt,
                new_submission,
                footer="Reply with y/n to confirm your preamble request.",
            )
        except ResponseTimedOut:
            return await ctx.error_reply("Prompt timed out, your preamble was not modified.")
        if not result:
            return await ctx.error_reply("Preamble replacement cancelled, your preamble was not modified.")

        await submit_preamble(ctx, ctx.author, new_submission, "User wishes to replace their preamble")
        return await ctx.reply(
            "Your preamble request has been sent to my managers for review.\n"
            "You will be messaged when your request is reviewed "
            "(usually around `1`-`2` hours, depending on availability).\n"
            f"If you wish to retract your submission, please use `{await ctx.best_prefix()}preamble --retract`.",
        )

    # Handle a request to add material to the preamble
    if flags["add"] or args:
        # Warn user before submitting another request if they already have one pending
        if pending_preamble:
            prompt = (
                "**Warning: You currently have a request awaiting review.**\n"
                "Sending another submission will **overwrite your previous request**, "
                "and you will lose your changes.\n"
                "Reply with `y` to proceed, or `n` to cancel."
            )
            try:
                response = await ctx.on_input(prompt, timeout=600)
            except ResponseTimedOut:
                return await ctx.error_reply("Query timed out, your preamble was not modified.")
            if response.lower() == "n":
                return await ctx.error_reply("Query cancelled, your preamble was not modified.")

        if not args:
            # Prompt the user for the material they wish to add, handle cancellations and timeout
            prompt = (
                "Please enter the material you wish to add to your preamble, or `c` to cancel.\n"
                f"**If you wish to *replace* your preamble, please rerun with `{await ctx.best_prefix()}preamble --replace`.**\n"
            )
            try:
                args = await ctx.on_input(prompt, timeout=600)
            except ResponseTimedOut:
                return await ctx.error_reply("Query timed out, your preamble was not modified.")
            if args.lower() == "c":
                return await ctx.error_reply("Query cancelled, your preamble was not modified.")

        new_submission = f"{preamble}\n{args}"

        # Check if the addition is a one line usepackage containing whitelisted packages
        args = args.strip()
        args = re.sub("(```)(tex|latex)*", "", args, flags=re.IGNORECASE)
        if "\n" not in args and args.startswith("\\usepackage"):
            packages = args[11:].strip(" {}").split(",")
            if all(not package.strip() or (package.strip() in whitelisted_packages) for package in packages):
                # All the requested packages are whitelisted
                # Update the preamble, log the changes, and notify the user
                preamble_data.insert(
                    allow_replace=True,
                    userid=ctx.author.id,
                    preamble=new_submission,
                    previous_preamble=preamble,
                )
                await ctx.reply("Your preamble has been updated!")
                await preamblelog(
                    ctx,
                    "Whitelisted packages were added to the preamble. New preamble below.",
                    source=new_submission,
                )
                return None

        # Set various warnings
        nonmatching_brackets = False
        duplicate_packages = False
        many_duplicates = False

        new_lines = new_submission.splitlines()

        duplicate_count = 0
        unique_lines = set()
        for line in new_lines:
            if len(line) > 5:
                if line in unique_lines:
                    duplicate_count += 1
                    if not duplicate_packages and line.strip().startswith("\\usepackage"):
                        duplicate_packages = True
                else:
                    unique_lines.add(line)
        many_duplicates = duplicate_count > 10
        nonmatching_brackets = not (
            (new_submission.count("(") == new_submission.count(")"))
            and (new_submission.count("{") == new_submission.count("}"))
        )
        warnings = []
        if nonmatching_brackets:
            warnings.append("Number of opening and closing brackets and parenthesis do not match!")
        if duplicate_packages:
            warnings.append("Duplicate package imports detected!")
        if many_duplicates:
            warnings.append("Many duplicate lines detected in submission!")
        warnings = "\n".join(warnings)

        # Confirm submission
        prompt = "Please confirm you want to submit the following preamble."
        try:
            result = await confirm(
                ctx,
                prompt,
                new_submission,
                start_page=-1,
                extra_fields=[("Warnings", warnings)] if warnings else None,
                footer="Reply with y/n to confirm your preamble request.",
            )
        except ResponseTimedOut:
            return await ctx.error_reply("Prompt timed out, your preamble was not modified.")
        if not result:
            return await ctx.error_reply("Preamble extension cancelled, your preamble was not modified.")

        await submit_preamble(
            ctx,
            ctx.author,
            new_submission,
            f"User wishes to add {len(args.splitlines())} lines to their preamble",
        )
        return await ctx.reply(
            "Your preamble request has been sent to my review team.\n"
            "You will be messaged when your request is reviewed "
            "(usually around `1`-`2` hours, depending on availability).\n"
            f"If you wish to retract your submission, please use `{await ctx.best_prefix()}preamble --retract`.",
        )

    # If the user doesn't want to edit their preamble, they must just want to view it

    title = f"{ctx.author.display_name}'s current preamble for LuaTeXit ({header})"
    return await view_preamble_v2(
        ctx,
        preamble,
        title,
        file_react=True,
        file_message=f"Current Preamble for {ctx.author}",
    )
