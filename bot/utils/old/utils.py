import asyncio
import datetime
import re
import subprocess

import discord
import iso8601


def load_into(bot):
    @bot.util
    def strfdelta(ctx, delta, sec=False, minutes=True, short=False):
        output = [[delta.days, "d" if short else " day"], [delta.seconds // 3600, "h" if short else " hour"]]
        if minutes:
            output.append([delta.seconds // 60 % 60, "m" if short else " minute"])
        if sec:
            output.append([delta.seconds % 60, "s" if short else " second"])
        for i in range(len(output)):
            if output[i][0] != 1 and not short:
                output[i][1] += "s"
        reply_msg = []
        if output[0][0] != 0:
            reply_msg.append(f"{output[0][0]}{output[0][1]} ")
        for i in range(1, len(output) - 1):
            reply_msg.append(f"{output[i][0]}{output[i][1]} ")
        if not short and reply_msg:
            reply_msg.append("and ")
        reply_msg.append(f"{output[len(output) - 1][0]}{output[len(output) - 1][1]}")
        return "".join(reply_msg)

    @bot.util
    async def run_sh(ctx, to_run):
        """
        Runs a command asynchronously in a subproccess shell.
        """
        process = await asyncio.create_subprocess_shell(to_run, stdout=asyncio.subprocess.PIPE)
        if ctx.bot.DEBUG > 2:
            await ctx.log(f"Running the shell command:\n{to_run}\nwith pid {str(process.pid)}")
        stdout, stderr = await process.communicate()
        if ctx.bot.DEBUG > 2:
            await ctx.log(
                "Completed the shell command:\n{}\n{}".format(to_run, "with errors." if process.returncode != 0 else "")
            )
        return stdout.decode(errors="backslashreplace").strip()

    @bot.util
    async def tail(ctx, filename, n):
        p1 = subprocess.Popen("tail -n " + str(n) + " " + filename, shell=True, stdin=None, stdout=subprocess.PIPE)
        out, err = p1.communicate()
        p1.stdout.close()
        return out.decode("utf-8")

    @bot.util
    def convdatestring(datestring):
        datestring = datestring.strip(" ,")
        datearray = []
        funcs = {"d": lambda x: x * 24 * 60 * 60, "h": lambda x: x * 60 * 60, "m": lambda x: x * 60, "s": lambda x: x}
        currentnumber = ""
        for char in datestring:
            if char.isdigit():
                currentnumber += char
            else:
                if currentnumber == "":
                    continue
                datearray.append((int(currentnumber), char))
                currentnumber = ""
        seconds = 0
        if currentnumber:
            seconds += int(currentnumber)
        for i in datearray:
            if i[1] in funcs:
                seconds += funcs[i[1]](i[0])
        return datetime.timedelta(seconds=seconds)

    @bot.util
    async def parse_flags(ctx, args, flags=[]):
        """
        Parses flags in args from the flags given in flags.
        Flag formats:
            'a': boolean flag, checks if present.
            'a=': Eats one "word"
            'a==': Eats all words up until next flag
        Returns a tuple (params, args, flags_present).
        flags_present is a dictionary {flag: value} with value being:
            False if a flag isn't present,
            the value of the flag for a long flag,
        If -- is present in the input as a word, all flags afterwards are ignored.
        TODO: Make this more efficient
        """
        # Split across whitespace, keeping the whitespace
        params = re.split(r"(\S+)", args)

        final_params = []  # Final list of command parameters, excluding flags and flag arguments
        final_flags = {}  # Dictionary of flags and flag values
        indexes = []  # Indices in the params list where the flags appear
        end_params = []  # The tail of the parameter list, after -- appears

        # Handle appearence of the flag terminator
        if "--" in params:
            i = params.index("--")
            end_params = params[i + 1 :] if i < len(params) - 1 else []
            params = params[:i]

        # Find the param indicies of the flags
        for flag in flags:
            clean_flag = flag.strip("=")

            if ("-" + clean_flag) in params:
                index = params.index("-" + clean_flag)
            elif ("--" + clean_flag) in params:
                index = params.index("--" + clean_flag)
            elif ("—" + clean_flag) in params:
                index = params.index("—" + clean_flag)
            else:
                final_flags[clean_flag] = False
                continue
            indexes.append((index, flag))

        # Sort the indicies to ensure we step through the flags in order of appearance
        indexes = sorted(indexes)

        # Add any parameters that appear before the first flag
        if len(indexes) > 0:
            final_params = params[0 : indexes[0][0]]
        else:
            final_params = params

        # Build the parameters and flag arguments
        for i, (index, flag) in enumerate(indexes):
            # Get the parameters between this flag and the next, or the end
            if len(params) > index + 1:
                if len(indexes) > i + 1:
                    flag_params = params[index + 1 : indexes[i + 1][0]]
                else:
                    flag_params = params[index + 1 :]
            else:
                flag_params = []

            # Split these into flag arguments and final parameters depending on flag type
            if flag.endswith("=="):
                flag_arg = "".join(flag_params).strip()
            elif flag.endswith("="):
                # Find the first non-whitespace param, if it exists
                j, arg = next(((j, arg) for j, arg in enumerate(flag_params) if arg.strip()), (len(flag_params), None))

                flag_arg = arg or ""

                # If there are any more params, add them to the final bunch
                if len(flag_params) > j + 1:
                    final_params.append("".join(flag_params[j + 1 :]).rstrip())
            else:
                flag_arg = True
                final_params.append("".join(flag_params).rstrip())

            # Set the flag arguments
            final_flags[flag.strip("=")] = flag_arg

        # Add any tail parameters
        final_params += end_params

        # Turn the parameter list into what we usually use, i.e. space split, and make the args
        final_args = "".join(final_params).strip()
        final_params = final_args.split(" ")
        return (final_params, final_args, final_flags)

    @bot.util
    async def emb_add_fields(ctx, embed, emb_fields):
        for field in emb_fields:
            embed.add_field(name=str(field[0]), value=str(field[1]), inline=bool(field[2]))

    @bot.util
    async def get_raw_cmds(ctx):
        handlers = ctx.bot.handlers
        cmds = {}
        for CH in handlers:
            cmds = dict(cmds, **(CH.raw_cmds))
        return cmds

    @bot.util
    async def pager(ctx, pages, embed=False, locked=True, destination=None, start_page=0, **kwargs):
        """
        Replies with the first page and provides reactions to page back and forth.
        Reaction timeout is five minutes.
        On timeout, returns the message (for easy deletion).
        pages is either a list of messages or a list of embeds, depending on the embed flag.
        """
        arg = "embed" if embed else "message"
        args = {}
        args[arg] = pages[start_page]
        if destination is None:
            out_msg = await ctx.reply(**args, **kwargs)
        else:
            out_msg = await ctx.send(destination, **args, **kwargs)

        if len(pages) == 1:
            return out_msg
        args = {}
        arg = "embed" if embed else "new_content"
        emo_next = ctx.bot.objects["emoji_next"]
        emo_prev = ctx.bot.objects["emoji_prev"]

        def check(reaction, user):
            return (
                (reaction.emoji in [emo_next, emo_prev])
                and (not (user == ctx.me))
                and (not locked or user == ctx.author)
            )

        try:
            await ctx.bot.add_reaction(out_msg, emo_prev)
            await ctx.bot.add_reaction(out_msg, emo_next)
        except discord.Forbidden:
            await ctx.reply("Cannot page results because I do not have permissions to add emojis!")
            return None

        async def paging():
            page = start_page
            while True:
                res = await ctx.bot.wait_for_reaction(message=out_msg, timeout=300, check=check)
                if res is None:
                    break
                try:
                    await ctx.bot.remove_reaction(out_msg, res.reaction.emoji, res.user)
                except discord.Forbidden:
                    pass
                page += 1 if res.reaction.emoji == emo_next else -1
                if page == -1:
                    page = len(pages) - 1
                if page == len(pages):
                    page = 0
                args[arg] = pages[page]
                await ctx.bot.edit_message(out_msg, **args)
            try:
                await ctx.bot.remove_reaction(out_msg, emo_prev, ctx.me)
                await ctx.bot.remove_reaction(out_msg, emo_next, ctx.me)
                await ctx.bot.clear_reactions(out_msg)
            except discord.Forbidden:
                pass
            except discord.NotFound:
                pass

        asyncio.ensure_future(paging())
        return out_msg

    @bot.util
    async def from_now(ctx, time_diff):
        now = discord.utils.utcnow().timestamp()
        return now + time_diff

    @bot.util
    async def to_tstamp(ctx, days=0, hours=0, minutes=0, seconds=0):
        return seconds + (minutes + (hours + days * 24) * 60) * 60

    @bot.util
    def parse_dur(ctx, time_str):
        funcs = {"d": lambda x: x * 24 * 60 * 60, "h": lambda x: x * 60 * 60, "m": lambda x: x * 60, "s": lambda x: x}
        time_str = time_str.strip(" ,")
        found = re.findall(r"(\d+)\s?(\w+?)", time_str)
        seconds = 0
        for bit in found:
            if bit[1] in funcs:
                seconds += funcs[bit[1]](int(bit[0]))
        return datetime.timedelta(seconds=seconds)

    @bot.util
    def prop_tabulate(ctx, prop_list, value_list):
        max_len = max(len(prop) for prop in prop_list)
        return "\n".join(
            [
                "`{}{}{}`\t{}".format(
                    "​ " * (max_len - len(prop)), prop, ":" if len(prop) > 1 else "​ " * 2, value_list[i]
                )
                for i, prop in enumerate(prop_list)
            ]
        )

    @bot.util
    def paginate_list(ctx, item_list, block_length=20, style="markdown", title=None):
        lines = ["{0:<5}{1:<5}".format(f"{i + 1}.", str(line)) for i, line in enumerate(item_list)]
        page_blocks = [lines[i : i + block_length] for i in range(0, len(lines), block_length)]
        pages = []
        for i, block in enumerate(page_blocks):
            pagenum = f"Page {i + 1}/{len(page_blocks)}"
            if title:
                header = f"{title} ({pagenum})" if len(page_blocks) > 1 else title
            else:
                header = pagenum
            header_line = "=" * len(header)
            full_header = f"{header}\n{header_line}\n" if len(page_blocks) > 1 or title else ""
            pages.append("```{}\n{}{}```".format(style, full_header, "\n".join(block)))
        return pages

    @bot.util
    def msg_string(ctx, msg, mask_link=False, line_break=False, tz=None, clean=True):
        timestr = "%I:%M %p, %d/%m/%Y"
        if tz:
            time = iso8601.parse_date(msg.timestamp.isoformat()).astimezone(tz).strftime(timestr)
        else:
            time = msg.timestamp.strftime(timestr)
        user = str(msg.author)
        attach_list = [attach["url"] for attach in msg.attachments if "url" in attach]
        if mask_link:
            attach_list = [f"[Link]({url})" for url in attach_list]
        attachments = "\nAttachments: {}".format(", ".join(attach_list)) if attach_list else ""
        return "`[{time}]` **{user}:** {line_break}{message} {attachments}".format(
            time=time,
            user=user,
            line_break="\n" if line_break else "",
            message=msg.clean_content if clean else msg.content,
            attachments=attachments,
        )

    @bot.util
    def msg_jumpto(ctx, msg):
        return "https://discordapp.com/channels/{}/{}/{}".format(
            msg.server.id if msg.server else "@me", msg.channel.id, msg.id
        )

    @bot.util
    async def get_avatar(ctx, user):
        if user.avatar:
            dancingpictures = "gif" if user.avatar.startswith("a_") else "png"
            avlink = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{dancingpictures}?size=2048"
        else:
            avlink = user.default_avatar_url
        return avlink

    @bot.util
    async def confirm_sent(ctx, msg=None, reply=None):
        try:
            await ctx.bot.add_reaction(msg if msg else ctx.msg, "✅")
        except discord.Forbidden:
            await ctx.reply(reply if reply else "Check your DMs!")

    @bot.util
    async def has_mod(ctx, user):
        (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
        return code == 0

    @bot.util
    def is_master(ctx, user):
        return int(user.id) in ctx.bot.bot_conf.getintlist("masters")

    @bot.util
    def is_exec(ctx, user):
        return ctx.is_master(user) or (int(user.id) in ctx.bot.bot_conf.getintlist("execWhiteList"))

    @bot.util
    def is_dev(ctx, user):
        return ctx.is_exec(user) or (int(user.id) in ctx.bot.bot_conf.getintlist("developers"))

    @bot.util
    def is_manager(ctx, user):
        return ctx.is_dev(user) or (int(user.id) in ctx.bot.bot_conf.getintlist("managers"))

    @bot.util
    async def offer_delete(ctx, out_msg, to_delete=None):
        if out_msg is None and to_delete is None:
            return
        mod_role = await ctx.server_conf.mod_role.get(ctx) if ctx.server else None

        if ctx.server:

            def check(reaction, user):
                if user == ctx.me:
                    return False
                result = user == ctx.author
                result = result or (mod_role and mod_role in [role.id for role in user.roles])
                result = result or user.server_permissions.administrator
                result = result or user.server_permissions.manage_messages
                result = result or user == ctx.server.owner
                return result

        else:

            def check(reaction, user):
                return user == ctx.author

        try:
            await ctx.bot.add_reaction(out_msg, ctx.bot.objects["emoji_delete"])
        except discord.Forbidden:
            return

        res = await ctx.bot.wait_for_reaction(
            message=out_msg, emoji=ctx.bot.objects["emoji_delete"], check=check, timeout=300
        )
        if res is None:
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_delete"], ctx.me)
            except Exception:
                pass
        elif res.reaction.emoji == ctx.bot.objects["emoji_delete"]:
            to_delete = to_delete if to_delete is not None else [out_msg]
            for msg in to_delete:
                try:
                    await ctx.bot.delete_message(msg)
                except Exception:
                    pass

    @bot.util
    async def find_message(ctx, msgid, chlist=None, ignore=[]):
        message = None
        chlist = ctx.server.channels if chlist is None else chlist

        for channel in chlist:
            if channel in ignore:
                continue
            if channel.type != discord.ChannelType.text:
                continue
            try:
                message = await ctx.bot.get_message(channel, msgid)
            except Exception:
                pass
            if message:
                break
        return message

    @bot.util
    def aemoji_mention(ctx, emoji):
        return f"<a:{emoji.name}:{emoji.id}>"

    @bot.util
    async def safe_delete_msgs(ctx, msgs):
        try:
            await asyncio.gather(*[ctx.bot.delete_message(msg) for msg in msgs])
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass
        except Exception:
            pass

    @bot.util
    def split_text(ctx, text, blocksize, code=True, syntax="", maxheight=50):
        """
        Break the text into blocks of maximum length blocksize
        If possible, break across nearby newlines. Otherwise just break at blocksize chars
        """
        blocks = []
        while True:
            if len(text) <= blocksize:
                blocks.append(text)
                break

            split_on = text[0:blocksize].rfind("\n")
            split_on = blocksize if split_on == -1 else split_on

            blocks.append(text[0:split_on])
            text = text[split_on:]

        # Add the codeblock ticks and the code syntax header, if required
        if code:
            blocks = [f"```{syntax}\n{block}\n```" for block in blocks]

        return blocks

    @bot.util
    async def soft_delete(ctx, msg):
        """
        Deletes the provided message if possible.
        Quietly exits if an expected error occurs.
        """
        try:
            await ctx.bot.delete_message(msg)
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass
