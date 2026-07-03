import asyncio
import datetime
import difflib
from collections.abc import Awaitable
from contextlib import suppress
from io import BytesIO
from pathlib import Path

import anyio
import discord
from cmdClient import Context  # noqa
from cmdClient.lib import ResponseTimedOut, SafeCancellation, UserCancelled
from constants import LuaTeXitCC
from discord import Member, User
from utils.lib import mail, split_text
from wards import is_reviewer

from modules.Tex.resources import default_preamble, failed_image_path

__location__ = str((Path.cwd() / Path(__file__).parent).resolve())

preamble_test_code = r"""
$98\%$ of $\mathbb{PEOPLE}$ can't solve \textbf{this}

\pdftexbanner
"""

preamble_test_code_luatex = r"""
\suppressmathparerror = 1
\luatexbanner

\texttt{U(no|)(sub|super)script}$\longrightarrow
    \psi\Usuperscript{1}\Usubscript{2} =
    \psi\Unosuperscript{1}\Unosubscript{2} =
    \psi\Unosuperscript{1}\Usubscript{2} =
    \psi\Usuperscript{1}\Unosubscript{2}
$
"""

preamble_test_code_xetex = r"""
This is Xe\TeX, Version \the\XeTeXversion\XeTeXrevision\ (\TeX\ Live $\the\year$)

\texttt{\textbackslash mdfivesum\{ABC\}}: \mdfivesum{ABC}
"""

# Load list of preamble presets from directory
# preset_dir = os.path.join(__location__, "presets")
# presets = [os.path.splitext(fn)[0] for fn in os.listdir(preset_dir) if fn.endswith('.tex')]
# presets_lower = [p.lower() for p in presets]


def tex_pagination(
    text,
    basetitle="",
    header=None,
    timestamp=True,
    author=None,
    time=None,
    colour=LuaTeXitCC["purple"],
    extra_fields=None,
    footer="",
):
    """
    Break up source LaTeX code into a number of embedded pages,
    with the code in codeblocks of maximum 1k chars
    """
    blocks = split_text(text, 1000, code=True, syntax="latex") if text else [None]

    # Change time to a datetime object if it isn't one
    if time is None:
        time = discord.utils.utcnow()
    elif isinstance(time, (float, int)):
        time = datetime.datetime.fromtimestamp(time, tz=discord.utils.utcnow().astimezone().tzinfo)

    blocknum = len(blocks)

    if blocknum == 1:
        block = blocks[0] or None
        desc = "{}\n{}".format(header, block or "") if header else (block or None)

        embed = discord.Embed(title=basetitle, color=colour, description=desc, timestamp=time)
        if author is not None:
            embed.set_author(name=author)
        if extra_fields is not None:
            for name, value in extra_fields:
                if name and value:
                    embed.add_field(name=name, value=value, inline=False)
        if footer is not None:
            embed.set_footer(text=footer)
        return [embed]

    embeds = []
    for i, block in enumerate(blocks):
        desc = f"{header}\n{block}" if header else block
        embed = discord.Embed(
            title=basetitle,
            colour=colour,
            # author=author,
            description=desc,
            timestamp=time,
        )
        embed.set_footer(text=f"{footer} Page {i + 1}/{blocknum}")
        if author is not None:
            embed.set_author(name=author)
        if extra_fields is not None:
            for name, value in extra_fields:
                if name and value:
                    embed.add_field(name=name, value=value, inline=False)
        embeds.append(embed)

    return embeds


async def tex_pagination_diff(
    text_old: str | None,
    tex_new: str,
    basetitle="",
    header: str | None = None,
    timestamp: bool = True,
    author: Member | User | None = None,
    time=None,
    colour=LuaTeXitCC["yellow"],
    extra_fields=None,
    footer="",
):
    """
    Run a `diff` on the old and new text, and view the result in a number of embedded pages.
    """
    if text_old is None:
        # if text_old is None, that means it's the default preamble
        # default preamble is in paradox/bot/modules/Tex/resources/default_preamble.tex
        default_preamble_path: str = str(Path("bot") / "modules" / "Tex" / "resources" / "default_preamble.tex")
        async with await anyio.open_file(default_preamble_path) as f:
            text_old = await f.read()

    diff = "\n".join(
        difflib.unified_diff(
            text_old.splitlines(keepends=False),
            tex_new.splitlines(keepends=False),
            fromfile="current preamble",
            tofile="pending preamble",
            lineterm="",
            n=0,
        ),
    )

    blocks = split_text(diff, 1000, code=True, syntax="diff") if diff else [None]

    # Change time to a datetime object if it isn't one
    if time is None:
        time = discord.utils.utcnow()
    elif isinstance(time, (float, int)):
        time = datetime.datetime.fromtimestamp(time, tz=discord.utils.utcnow().astimezone().tzinfo)

    blocknum = len(blocks)

    if blocknum == 1:
        block = blocks[0] or None
        desc = "{}\n{}".format(header, block or "") if header else (block or None)

        embed = discord.Embed(title=basetitle, color=colour, description=desc, timestamp=time)
        if author is not None:
            embed.set_author(name=author)
        if extra_fields is not None:
            for name, value in extra_fields:
                if name and value:
                    embed.add_field(name=name, value=value, inline=False)
        if footer is not None:
            embed.set_footer(text=footer)
        return [embed]

    embeds = []
    for i, block in enumerate(blocks):
        desc = f"{header}\n{block}" if header else block
        embed = discord.Embed(
            title=basetitle,
            colour=colour,
            # author=author,
            description=desc,
            timestamp=time,
        )
        embed.set_footer(text=f"{footer} Page {i + 1}/{blocknum}")
        if author is not None:
            embed.set_author(name=author)
        if extra_fields is not None:
            for name, value in extra_fields:
                if name and value:
                    embed.add_field(name=name, value=value, inline=False)
        embeds.append(embed)

    return embeds


async def sendfile_reaction_handler(ctx: Context, msg, contents, title, file_name="preamble.tex"):
    """
    Attach a reaction to the given message which sends reacting users
    a file containing `contents`.
    """
    emoji = ctx.client.conf.emojis.getemoji("sendfile")
    try:
        await msg.add_reaction(emoji)
    except discord.Forbidden:
        return
    except discord.NotFound:
        return

    # Generate file
    temp_file = BytesIO()
    temp_file.write(contents.encode())

    def _check(reaction, user):
        return reaction.message.id == msg.id and reaction.emoji == emoji

    while True:
        try:
            _, user = await ctx.client.wait_for("reaction_add", check=_check, timeout=300)
        except asyncio.TimeoutError:
            break

        if user != ctx.client.user:
            try:
                temp_file.seek(0)
                dFile = discord.File(temp_file, filename=file_name)
                await asyncio.gather(user.send(file=dFile, content=title), msg.remove_reaction(emoji, user))
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass
    try:
        await msg.clear_reaction(emoji)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass

    temp_file.close()


async def view_preamble(
    ctx: Context,
    preamble: str,
    title: str,
    start_page=0,
    file_react=False,
    file_message=None,
    **pagination_args,
) -> Awaitable[discord.Message | None]:
    pages = tex_pagination(preamble, basetitle=title, **pagination_args)
    out_msg = await ctx.pager(pages, start_page=start_page, locked=False)

    if file_react and out_msg is not None:
        # Add the sendfile reaction if required
        task = asyncio.ensure_future(sendfile_reaction_handler(ctx, out_msg, preamble, file_message or title))
        task.cancel()  # Don't wait for it to finish, just let it run in the background

    return out_msg


async def view_preamble_v2(
    ctx: Context,
    preamble: str,
    title: str,
    file_react=False,
    file_message=None,
):
    out_msg = await ctx.pager_v2(
        content=preamble,
        title=title,
        code=True,
        syntax="latex",
        block_length=1500,
        maxheight=30,
    )

    if file_react and out_msg is not None:
        # Add the sendfile reaction if required
        task = asyncio.ensure_future(sendfile_reaction_handler(ctx, out_msg, preamble, file_message or title))
        task.cancel()  # Don't wait for it to finish, just let it run in the background

    return out_msg


async def view_preamble_diff(
    ctx: Context,
    preamble_old: str,
    preamble_pending: str,
    title: str,
    start_page=0,
    file_react: bool = False,
    file_message=None,
    **pagination_args,
):
    pages = await tex_pagination_diff(preamble_old, preamble_pending, basetitle=title, **pagination_args)

    return await ctx.pager(pages, start_page=start_page, locked=False)


async def confirm(ctx: Context, question: str, preamble: str, **kwargs):
    out_msg = await view_preamble(ctx, preamble, f"{question} (y/n)", **kwargs)
    result_msg = await ctx.listen_for(["y", "yes", "n", "no"], timeout=120)

    result = result_msg.content.lower()
    with suppress(Exception):
        await out_msg.delete()
        await result_msg.delete()

    return result not in ["n", "no"]


async def preamblelog(ctx: Context, title: str | None, user=None, userid=None, author=None, header=None, source=None):
    """
    Log a message to the preamble log channel
    """
    logchid = int(ctx.client.conf.get("preamble_logch"))

    user = user or ctx.author
    author = author or f"{user} ({user.id})"

    content = "{}\n{}\n{}".format(title or "", header or "", author or "")
    if source:
        with BytesIO() as temp_file:
            temp_file.write(source.encode())
            temp_file.seek(0)
            dfile = discord.File(temp_file, filename=f"{userid or user.id}.tex")
            await mail(ctx.client, logchid, content=content, file=dfile)
    else:
        await mail(ctx.client, logchid, content=content)


#     pages = tex_pagination(source, basetitle=title, header=header, author=author)

#     if source is None:
#         await ctx.pager(pages, embed=True, locked=False, destination=logch)
#     else:
#         with BytesIO() as temp_file:
#             temp_file.write(source.encode())
#             temp_file.seek(0)
#             await ctx.pager(
#                 pages, embed=True, locked=False, destination=logch, file_data=temp_file, file_name="source.tex"
#             )


async def resolve_pending_preamble(ctx, userid, info, colour=None):
    """
    Clean up after a preamble submission request has been handled
    Involves finding the message in the submission log,
    clearing the reactions and editing it.
    """
    #     # Retrieve the pending preamble info
    #     info_pack = await ctx.bot.data.users.get(userid, "pending_preamble_info")

    #     # Return if there is no pending preamble
    #     if not info_pack:
    #         return

    #     # Retrieve the message id of the submission message
    #     msgid = info_pack[2]

    #     # Find the message in the submission channel
    #     subch = ctx.bot.objects["latex_preamble_subch"]
    #     try:
    #         msg = await ctx.bot.get_message(subch, msgid)
    #     except discord.NotFound:
    #         # The message wasn't found, just return silently, nothing to do
    #         return
    #     except Exception:
    #         # Various things could go wrong here
    #         # This step isn't crucial and we don't want to expose it to the user, so fail silently for now
    #         # TODO: Log this
    #         return

    #     # Remove all the reactions on the message
    #     await ctx.bot.clear_reactions(msg)

    #     # Edit the message with the provided info
    #     await ctx.bot.edit_message(msg, new_content=info)
    #     if colour is not None:
    #         embed = msg.embeds[0]
    #         msg_embed = discord.Embed.from_data(embed)
    #         msg_embed.colour = colour
    #         await ctx.bot.edit_message(msg, embed=msg_embed)


async def submit_preamble(ctx: Context, user, submission, info):
    """
    Make a new preamble submission
    """
    # Submit the request
    ctx.client.data.user_pending_preambles.insert(
        allow_replace=True,
        userid=user.id,
        app=ctx.client.app,
        username=user.name,
        pending_preamble=submission,
        submission_time=int(discord.utils.utcnow().timestamp()),
        submission_summary=info,
        submission_source_id=ctx.author.id if not ctx.guild else ctx.guild.id,
        submission_source_name="DM" if not ctx.guild else ctx.guild.name,
    )

    # Mail in the submission
    subchid = int(ctx.client.conf.get("preamble_subch"))

    with BytesIO() as temp_file:
        temp_file.write(submission.encode())
        temp_file.seek(0)
        dfile = discord.File(temp_file, filename=f"{user.id}.tex")
        await mail(ctx.client, subchid, content=f"New submission from {user} `uid:{user.id}`", file=dfile)


#     # Mark any previous preamble request as outdated
#     await handled_preamble(ctx, user.id, "New preamble request submitted", colour=discord.Colour.red())

#     # Set the new pending preamble
#     await ctx.data.users_long.set(ctx.authid, "pending_preamble", submission)

#     # Send the preamble request to the submission channel
#     title = "New preamble submission!"
#     author = "{} ({})".format(user, user.id)
#     time = discord.utils.utcnow()

#     submission_channel = ctx.bot.objects["latex_preamble_subch"]
#     sub_msg = await view_preamble(ctx, submission, title, start_page=-1,
#                                   author=author, time=time, header=info,
#                                   destination=submission_channel)

#     # Store the pending preamble info
#     info_pack = (datetime.datetime.timestamp(time), info, sub_msg.id)
#     await ctx.data.users.set(ctx.authid, "pending_preamble_info", info_pack)

#     # Add the approval/denial/testing emojis to the submission
#     # Create a new context so the judgement process doesn't interfere with the original user
#     newctx = ctx.bot.make_msgctx(channel=submission_channel)
#     asyncio.ensure_future(judgement_reactions(newctx, user.id, sub_msg))


async def judgement_reactions(ctx: Context, userid, msg):
    """
    Adds approve/deny/test reactions to the given msg,
    with the reactions applicable to the user given by the userid.
    Returns:
        None, if the userid is no longer in the pending preamble list,
        True, if the preamble was approved,
        False, if the preamble was denied.
    """
    # Check that the context author has preamble reviewer permissions
    if not await is_reviewer.run(ctx):
        raise ValueError("Attempt to add judgement reactions for non-reviewer.")

    # Load reaction emojis
    approve = ctx.client.conf.emojis.getemoji("approve")
    deny = ctx.client.conf.emojis.getemoji("deny")
    test = ctx.client.conf.emojis.getemoji("test")

    # Checks whether the emoji is valid and whether the user is the caller
    def _check(reaction, user):
        return (reaction.emoji in [approve, deny, test]) and user == ctx.author and reaction.message == msg

    # Add the reactions, if possible
    try:
        await msg.add_reaction(approve)
        await msg.add_reaction(deny)
        await msg.add_reaction(test)
    except discord.Forbidden:
        return None

    # Reaction action loop
    while True:
        try:
            reaction, _ = await ctx.client.wait_for("reaction_add", check=_check, timeout=600)
        except asyncio.TimeoutError:
            # If the user still has a pending preamble, continue the loop
            if ctx.client.data.user_pending_preambles.select_where(userid=userid):
                continue
            # Otherwise, remove the reactions and return
            with suppress(Exception):
                await msg.remove_reaction(approve, ctx.client.user)
                await msg.remove_reaction(deny, ctx.client.user)
                await msg.remove_reaction(test, ctx.client.user)
            break

        # If the user no longer has a pending preamble, let the reviewer know and exit
        if not ctx.client.data.user_pending_preambles.select_where(userid=userid):
            await ctx.reply("Submission no longer exists!")
            return None

        # Handle the reacted emoji as appropriate
        if reaction.emoji == approve:
            if await approve_submission(ctx, userid, ctx.author):
                return True
        elif reaction.emoji == deny:
            if await deny_submission(ctx, userid, ctx.author):
                return False
        elif reaction.emoji == test:
            await test_submission(ctx, userid, ctx.author)


async def approve_submission(ctx: Context, userid, manager, reason=None):
    ctx.author = manager  # Hack so that ask and input work properly

    # Ask for confirmation and potential new message
    # Create default approval message
    default_msg = "Your recent request for a LaTeX preamble submission has been approved!\
        \nYour preamble has been modified and may be seen using the `preamble` command.\
        \nShould you wish to revert these changes, please use `preamble --revert`."
    embed = discord.Embed(title="Preamble request approval", description=default_msg)
    embed.timestamp = discord.utils.utcnow()

    # If the user no longer has a pending preamble, let the reviewer know and exit
    if not ctx.client.data.user_pending_preambles.select_where(userid=userid):
        await ctx.error_reply("Submission no longer exists!")
        return None

    # Check whether this needs editing
    if reason:
        embed.add_field(name="Reviewer comments", value=reason)
        preview = await ctx.reply(content="Approving preamble...", embed=embed)
    else:
        preview = await ctx.reply(
            content=(
                "Do you wish to add an additional message (automatically sends in 20s)? (`y(es)`/`n(o)`/`c(ancel)`)"
            ),
            embed=embed,
        )
        try:
            result_msg = await ctx.listen_for(("y", "yes", "n", "no", "c", "cancel"), timeout=20)
            resp = result_msg.content.lower()
            with suppress(Exception):
                await result_msg.delete()
        except ResponseTimedOut:
            resp = None

        if resp is None or resp.startswith("n"):
            # Send message as-is
            pass
        elif resp.startswith("c"):
            await preview.edit(content="Preamble approval cancelled on manager request.")
            raise UserCancelled("Cancelling preamble approval.")
        elif resp.startswith("y"):
            # Ask for the new field
            try:
                result = await ctx.on_input(
                    "Please enter the additional approval message, or `c` to cancel!",
                    timeout=600,
                )
            except ResponseTimedOut:
                await preview.edit(content="Preamble approval cancelled due to query timeout.")
                raise ResponseTimedOut("Query timed out, aborting preamble approval.") from None
            if result.lower() in ["c", "cancel"]:
                await preview.edit(content="Preamble approval cancelled on manager request.")
                raise UserCancelled("Cancelling preamble approval.")

            # Update the embed with the new field
            embed.add_field(name="Reviewer comments", value=result)

    # Approve the preamble
    pending_info = ctx.client.data.user_pending_preambles.select_where(userid=userid)
    if not pending_info:
        await preview.edit(content="User no longer has a pending preamble to approve! Cancelling.")
        raise SafeCancellation

    current_info = ctx.client.data.user_latex_preambles.select_where(userid=userid)
    previous_preamble = current_info[0]["preamble"] if current_info else default_preamble
    ctx.client.data.user_latex_preambles.insert(
        allow_replace=True,
        userid=userid,
        preamble=pending_info[0]["pending_preamble"],
        previous_preamble=previous_preamble,
    )
    ctx.client.data.user_pending_preambles.delete_where(userid=userid)
    await resolve_pending_preamble(
        ctx,
        userid,
        f"Preamble approved by {manager.mention}",
        colour=discord.Colour.green(),
    )
    await preamblelog(
        ctx,
        f"Preamble request approved by {manager} ({manager.id})",
        author="{} ({})".format(pending_info[0]["username"], userid),
        userid=userid,
        source=pending_info[0]["pending_preamble"],
    )

    # Update the preview
    await preview.edit(
        content="Approved preamble, sending approval message {}".format(ctx.client.conf.emojis.getemoji("loading")),
        embed=embed,
    )

    # Try and DM the user with their happy news
    # First find the user
    user = ctx.client.get_user(userid)
    if user is None:
        try:
            user = await ctx.client.fetch_user(userid)
        except discord.NotFound:
            await preview.edit(content="Approved, but user not known to Discord, couldn't send the approval message.")

    try:
        await user.send(embed=embed, content=user.mention)
    except discord.Forbidden:
        await preview.edit(
            content=(
                "Approved, but Discord didn't let me DM the user. "
                "I might not be able to see them (no shared guilds), or they might have blocked me."
            ),
        )
    except Exception as e:
        await preview.edit(content=("Approved, but something unexpected occurred while sending the approval message."))
        raise e
    else:
        await preview.edit(content=(f"Preamble approved! Good work, <@{manager.id}>!"))
    return True


async def deny_submission(ctx: Context, userid, manager, reason=None):
    ctx.author = manager  # Hack so that ask and input work properly

    # If the user no longer has a pending preamble, let the reviewer know and exit
    if not ctx.client.data.user_pending_preambles.select_where(userid=userid):
        await ctx.error_reply("Submission no longer exists!")
        return None

    # Create base denial message
    default_msg = (
        "Your recent request for a LaTeX preamble submission was denied!\n"
        "If you want assistance setting your preamble, please join our [support guild]({})."
    ).format(ctx.client.app_info["support_guild"])
    embed = discord.Embed(title="Preamble request rejection", description=default_msg)
    embed.timestamp = discord.utils.utcnow()

    # Check whether this needs editing
    if reason is None:
        preview = await ctx.reply(content="Please enter the rejection reason, or send `c` to cancel!", embed=embed)
        try:
            result = await ctx.on_input(preview, delete_after=False, timeout=600)
        except ResponseTimedOut:
            await preview.edit(content="Preamble rejection cancelled due to query timeout.")
            return None
        if result.lower() in ["c", "cancel"]:
            await preview.edit(content="Preamble rejection cancelled on manager request.")
            raise UserCancelled("Cancelling preamble rejection.")

        # Update the embed with the new field
        embed.add_field(name="Reason", value=result)
    else:
        embed.add_field(name="Reason", value=reason)
        preview = await ctx.reply(content="Denying preamble.", embed=embed)

    # Deny the preamble
    pending_info = ctx.client.data.user_pending_preambles.select_where(userid=userid)
    if not pending_info:
        await preview.edit(content="User no longer has a pending preamble to deny! Cancelling.")
        raise SafeCancellation

    ctx.client.data.user_pending_preambles.delete_where(userid=userid)
    await resolve_pending_preamble(ctx, userid, f"Preamble denied by {manager.mention}", colour=discord.Colour.red())
    await preamblelog(
        ctx,
        f"Preamble request denied by {manager} ({manager.id})",
        author="{} ({})".format(pending_info[0]["username"], userid),
        userid=userid,
        source=pending_info[0]["pending_preamble"],
    )

    # Update the preview
    await preview.edit(
        content="Denied preamble, sending rejection message {}".format(ctx.client.conf.emojis.getemoji("loading")),
        embed=embed,
    )

    # First find the user
    user = ctx.client.get_user(userid)
    if user is None:
        try:
            user = await ctx.client.fetch_user(userid)
        except discord.NotFound:
            await preview.edit(content="Denied, but user not known to Discord, couldn't send the rejection message.")

    try:
        await user.send(embed=embed, content=user.mention)
    except discord.Forbidden:
        await preview.edit(
            content=(
                "Denied, but Discord didn't let me DM the user. "
                "I might not be able to see them (no shared guilds), or they might have blocked me."
            ),
        )
    except Exception as e:
        await preview.edit(content=("Denied, but something unexpected occurred while sending the rejection message."))
        raise e
    else:
        await preview.edit(content=(f"Preamble denied! Good work, <@{manager.id}>!"))
    return True


async def test_submission(ctx, userid, manager):
    """
    Compile a piece of test LaTeX to test the provided userid's preamble.
    Replies with the compiled LaTeX output, and any error that occurs.
    """
    # Separate staging folder for testing purposes
    testid = manager.id * 1000

    # Retrieve the pending preamble if it exists, otherwise return
    pending_info = ctx.client.data.user_pending_preambles.select_where(userid=userid)
    if not pending_info:
        await ctx.error_reply("User no longer has a pending preamble to test! Cancelling.")
        raise SafeCancellation
    preamble = pending_info[0]["pending_preamble"]

    # Compile the latex with this preamble
    # Construct a for loop for testing, embedding and logging three LaTeX engines
    engines = ["pdfLaTeX", "XeLaTeX", "LuaLaTeX"]
    file_path = f"tex/staging/{testid}/{testid}.png"

    for engine in engines:
        match engine.lower():
            case "pdflatex":
                log = await ctx.maketex(preamble_test_code, testid, preamble=preamble)

                dfile = (
                    discord.File(file_path)
                    if await anyio.Path(file_path).is_file()
                    else discord.File(failed_image_path)
                )

                if not log:
                    message = f"""No errors for {engine} and pending preamble of {userid}"""
                    await ctx.reply(content=message, file=dfile)
                else:
                    message = f"""Error(s) found: {engine} and pending preamble of {userid}"""
                    embed = discord.Embed(description=f"```\n{log}\n```")
                    await ctx.reply(content=message, file=dfile, embed=embed)
            case "lualatex":
                log = await ctx.makeluatex(preamble_test_code_luatex, testid, preamble=preamble)

                dfile = (
                    discord.File(file_path)
                    if await anyio.Path(file_path).is_file()
                    else discord.File(failed_image_path)
                )

                if not log:
                    message = f"""No errors for {engine} and pending preamble of {userid}"""
                    await ctx.reply(content=message, file=dfile)
                else:
                    message = f"""Error(s) found: {engine} and pending preamble of {userid}"""
                    embed = discord.Embed(description=f"```\n{log}\n```")
                    await ctx.reply(content=message, file=dfile, embed=embed)
            case "xelatex":
                log = await ctx.makexetex(preamble_test_code_xetex, testid, preamble=preamble)

                dfile = (
                    discord.File(file_path)
                    if await anyio.Path(file_path).is_file()
                    else discord.File(failed_image_path)
                )

                if not log:
                    message = f"""No errors for {engine} and pending preamble of {userid}"""
                    await ctx.reply(content=message, file=dfile)
                else:
                    message = f"""Error(s) found: {engine} and pending preamble of {userid}"""
                    embed = discord.Embed(description=f"```\n{log}\n```")
                    await ctx.reply(content=message, file=dfile, embed=embed)
