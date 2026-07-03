import asyncio
import string

import discord
from paraCH import paraCH

cmds = paraCH()

from cmdClient import Context  # noqa


discordColours = {
    "blue": discord.Colour.dark_purple(),  # #71368A
    "blurple": discord.Colour.blurple(),  # #5865F2
    "brand green": discord.Colour.brand_green(),  # #57F287
    "brand red": discord.Colour.brand_red(),  # #ED4245
    "dark blue": discord.Colour.dark_blue(),  # #206694
    "dark embed": discord.Colour.dark_embed(),  # #2B2D31
    "dark gold": discord.Colour.dark_gold(),  # #C27C0E
    "dark green": discord.Colour.dark_green(),  # #1F8B4C
    "dark grey": discord.Colour.dark_grey(),  # #607d8b
    "dark magenta": discord.Colour.dark_magenta(),  # #AD1457
    "dark orange": discord.Colour.dark_orange(),  # #A84300
    "dark purple": discord.Colour.dark_purple(),  # #71368A
    "dark red": discord.Colour.dark_red(),  # #992D22
    "dark teal": discord.Colour.dark_teal(),  # #11806A
    "darker grey": discord.Colour.darker_grey(),  # #546e7a
    "fuchsia": discord.Colour.fuchsia(),  # #EB459E
    "gold": discord.Colour.gold(),  # #F1C40F
    "green": discord.Colour.green(),  # #2ECC71
    "light grey": discord.Colour.light_grey(),  # #979C9F
    "lighter grey": discord.Colour.lighter_grey(),  # #95A5A6
    "magenta": discord.Colour.magenta(),  # #E91E63
    "og blurple": discord.Colour.og_blurple(),  # #7289DA
    "orange": discord.Colour.orange(),  # #E67E22
    "pink": discord.Colour.pink(),  # #EB459F
    "purple": discord.Colour.purple(),  # #9B59B6
    "random": discord.Colour.random(),
    "red": discord.Colour.red(),  # #E74C3C
    "teal": discord.Colour.teal(),  # #1ABC9C
    "yellow": discord.Colour.yellow(),  # #FEE75C
}


root_menu = []
field_menu = []


# Define callback functions for the menu


async def update_preview(ctx: Context):
    try:
        await ctx.bot.edit_message(ctx.objs["embed_preview_msg"], embed=ctx.objs["embed_embed"])
    except discord.HTTPException:
        await ctx.bot.edit_message(
            ctx.objs["embed_preview_msg"],
            "This embed contains errors and cannot be updated! Please re-enter your last input.",
        )


async def root_callback(ctx: Context, result):
    await root_menu[result][1](ctx)
    asyncio.ensure_future(update_preview(ctx))


async def field_callback(ctx: Context, result):
    await field_menu[result][1](ctx)
    asyncio.ensure_future(update_preview(ctx))


# Define menu items


def menu_item(item_list, item_name):
    def wrapper(func):
        item_list.append((item_name, func))

    return wrapper


@menu_item(root_menu, "Set Title")
async def set_title(ctx):
    await ctx.bot.edit_message(
        ctx.objs["menu"]["msg"],
        "Please enter the title! (Max 256 characters, type c to cancel.)",
    )

    output = await ctx.wait_for_string(max_len=256)
    if output is not None:
        ctx.objs["embed_embed"].title = output


@menu_item(root_menu, "Set Author")
async def set_author(ctx: Context):
    new_msg = "Please enter the author name! (Max 256 characters, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    new_author = await ctx.wait_for_string(max_len=256)
    if new_author is not None:
        ctx.objs["embed_embed"].set_author(
            name=new_author,
            url=ctx.objs["embed_embed"].author.url,
            icon_url=ctx.objs["embed_embed"].author.icon_url,
        )


@menu_item(root_menu, "Set Author Icon")
async def set_author_icon(ctx: Context):
    new_msg = "Please submit the author icon! (Must be a valid URL, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].set_author(
            name=ctx.objs["embed_embed"].author.name,
            url=ctx.objs["embed_embed"].author.url,
            icon_url=output,
        )


@menu_item(root_menu, "Set Author URL")
async def set_author_url(ctx: Context):
    new_msg = "Please enter the author URL! (Must be a valid URL, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].set_author(
            name=ctx.objs["embed_embed"].author.name,
            url=output,
            icon_url=ctx.objs["embed_embed"].author.icon_url,
        )


def colour_check(ctx: Context, msg: str):
    user_str = msg.content
    if user_str.lower() in discordColours:
        return None
    user_str = user_str.strip("#")
    if len(user_str) != 6 or not all(c in string.hexdigits for c in user_str):
        return "Colour not recognised!"
    return None


@menu_item(root_menu, "Set Colour")
async def set_colour(ctx):
    new_msg = "Please enter a colour! (Either a valid hex code or a named colour, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string(check=colour_check)
    if output is not None:
        if output.lower() in discordColours:
            colour = discordColours[output.lower()]
        else:
            colour = discord.Colour(int(output.strip("#"), 16))

        ctx.objs["embed_embed"].colour = colour


@menu_item(root_menu, "Set URL")
async def set_url(ctx):
    new_msg = "Please enter the url! (Must be a valid url, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].url = output


@menu_item(root_menu, "Set Description")
async def set_description(ctx):
    new_msg = "Please enter the description! (Type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].description = output


@menu_item(root_menu, "Set Image")
async def set_image(ctx):
    new_msg = "Please submit the embed image! (Must be a valid URL, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    new_image = await ctx.wait_for_string()
    if new_image is not None:
        ctx.objs["embed_embed"].set_image(url=new_image)


@menu_item(root_menu, "Set Thumbnail")
async def set_thumbnail(ctx):
    new_msg = "Please submit the thumbnail image! (Must be a valid URL, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    new_image = await ctx.wait_for_string()
    if new_image is not None:
        ctx.objs["embed_embed"].set_thumbnail(url=new_image)


@menu_item(root_menu, "Set Footer Text")
async def set_footer(ctx):
    new_msg = "Please enter the footer text! (Type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].set_footer(text=output, icon_url=ctx.objs["embed_embed"].footer.icon_url)


@menu_item(root_menu, "Set Footer Icon")
async def set_footer_icon(ctx):
    new_msg = "Please submit the footer image! (Must be a valid URL, type c to cancel.)"
    await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

    output = await ctx.wait_for_string()
    if output is not None:
        ctx.objs["embed_embed"].set_footer(text=ctx.objs["embed_embed"].footer.text, icon_url=output)


@menu_item(root_menu, "Modify Fields")
async def field_edit(ctx):
    await ctx.menu(
        [item[0] for item in field_menu],
        field_callback,
        menu_msg=ctx.objs["menu"]["msg"],
        title="Embed Editor -> Modify Fields",
        prompt="Please type the number of your selection:",
    )


@menu_item(root_menu, "Save and Exit")
async def save_and_exit(ctx):
    server_embeds = await ctx.data.servers_long.get(ctx.server.id, "server_embeds")
    server_embeds = server_embeds or {}
    if ctx.objs.get("embed_name"):
        embed_name = ctx.objs["embed_name"]
    else:
        new_msg = "Please enter a short name for this embed, for viewing and editing."
        await ctx.bot.edit_message(ctx.objs["menu"]["msg"], new_msg)

        embed_name = await ctx.wait_for_string()

    if embed_name is not None:
        if embed_name in server_embeds:
            resp = await ctx.ask(f"Are you sure you want to overwrite the stored embed `{embed_name}`?")
            if resp is None or resp == 0:
                return
        server_embeds[embed_name] = ctx.objs["embed_embed"].to_dict()
        try:
            await ctx.data.servers_long.set(ctx.server.id, "server_embeds", server_embeds)
            await ctx.reply(
                f"The embed has been saved!\n To view the embed use `{ctx.used_prefix}embed {embed_name}`, and reopen the Embed Editor with `{ctx.used_prefix}editembed {embed_name}`.",
            )
        except Exception:
            await ctx.reply(
                "Sorry, you have exceeded the total embed size limit for this server! Your embed couldn't be saved.",
            )
        await ctx.bot.edit_message(ctx.objs["embed_preview_msg"], " ")
        asyncio.ensure_future(ctx.offer_delete(ctx.objs["embed_preview_msg"]))
        ctx.objs["menu"]["done"] = True


@menu_item(root_menu, "Exit without saving")
async def exit_no_save(ctx):
    ctx.objs["menu"]["done"] = True


async def ask_for_field(ctx):
    field = {"name": None, "value": None, "inline": None}
    await ctx.bot.edit_message(
        ctx.objs["menu"]["msg"],
        "Please enter the field name. (256 characters max, press c to cancel.))",
    )
    field_name = await ctx.wait_for_string(max_len=256)
    if field_name is None:
        return None
    field["name"] = field_name

    await ctx.bot.edit_message(
        ctx.objs["menu"]["msg"],
        "Please enter the field value. (1024 characters max, press c to cancel.))",
    )
    field_value = await ctx.wait_for_string(max_len=1024)
    if field_value is None:
        return None
    field["value"] = field_value

    inline = await ctx.ask("Should the field be displayed inline?", use_msg=ctx.objs["menu"]["msg"])
    if inline is None:
        return None
    field["inline"] = inline == 1
    return field


@menu_item(field_menu, "Add field")
async def add_field(ctx):
    field = await ask_for_field(ctx)
    if field is not None:
        ctx.objs["embed_embed"].add_field(name=field["name"], value=field["value"], inline=field["inline"])


@menu_item(field_menu, "Remove Field")
async def remove_field(ctx):
    fields = ctx.objs["embed_embed"].fields
    if not fields:
        await ctx.bot.edit_message(ctx.objs["menu"]["msg"], "There are no fields to remove! Type anything to continue.")
        await ctx.wait_for_string()
        return

    result = await ctx.silent_selector(
        "Please select a field to remove",
        [field.name for field in fields],
        use_msg=ctx.objs["menu"]["msg"],
    )
    if result is None:
        return

    ctx.objs["embed_embed"].remove_field(result)


@menu_item(field_menu, "Edit Field")
async def edit_field(ctx):
    fields = ctx.objs["embed_embed"].fields
    if not fields:
        await ctx.bot.edit_message(ctx.objs["menu"]["msg"], "There are no fields to edit! Type anything to continue.")
        await ctx.wait_for_string()
        return

    result = await ctx.silent_selector(
        "Please select a field to edit",
        [field.name for field in fields],
        use_msg=ctx.objs["menu"]["msg"],
    )
    if result is None:
        return

    field = await ask_for_field(ctx)
    if field is not None:
        ctx.objs["embed_embed"].set_field_at(result, name=field["name"], value=field["value"], inline=field["inline"])


@menu_item(field_menu, "Back to Embed Editor")
async def go_back(ctx):
    ctx.objs["menu"]["done"] = True


async def init_embed(ctx):
    embed = discord.Embed()
    embed.colour = discord.Colour(int("33353c", 16))
    ctx.objs["embed_preview_msg"] = await ctx.reply("Preview:", embed=embed)
    ctx.objs["embed_embed"] = embed


async def get_server_embed(ctx, emb_name):
    server_embeds = await ctx.data.servers_long.get(ctx.server.id, "server_embeds")
    if not server_embeds:
        await ctx.reply(
            f"There are no saved embeds in this server! Moderators may create embeds using `{ctx.used_prefix}buildembed`",
        )
        return None
    if emb_name == "":
        keys = list(server_embeds.keys())
        result = await ctx.selector("Please select an embed!", keys)
        if result is None:
            return None
        name = keys[result]
    elif emb_name not in server_embeds:
        await ctx.reply(f"No embed exists with this name! Use `{ctx.used_prefix}embed` to see a list of embeds.")
        return None
    else:
        name = emb_name

    embed = server_embeds[name]
    proper_embed = discord.Embed.from_data(embed)
    if "footer" in embed:
        proper_embed._footer = embed["footer"]
    if "image" in embed:
        proper_embed._image = embed["image"]
    return name, proper_embed


@cmds.cmd(
    "buildembed",
    category="Server Admin",
    short_help="Interactively build an embed to be retrieved later",
    aliases=["editembed", "embededitor"],
    flags=["delete"],
)
@cmds.require("in_server")
@cmds.require("in_server_has_mod")
async def cmd_buildembed(ctx):
    """
    Usage:
        {prefix}buildembed
        {prefix}editembed <embedname>
        {prefix}editembed --delete <embedname>
    Description:
        Interactively creates or edits an embed which may be used elsewhere in the server.
        May also be used to delete an existing embed by name
    """
    if ctx.flags["delete"]:
        fetch_embed = await get_server_embed(ctx, ctx.arg_str)
        if fetch_embed is None:
            return

        server_embeds = await ctx.data.servers_long.get(ctx.server.id, "server_embeds")
        server_embeds.pop(fetch_embed[0], None)
        await ctx.data.servers_long.set(ctx.server.id, "server_embeds", server_embeds)
        await ctx.reply(f"Deleted embed `{fetch_embed[0]}`!")
    else:
        if ctx.used_cmd_name.lower() == "buildembed":
            ctx.objs["embed_preview"] = await init_embed(ctx)
        else:
            fetch_embed = await get_server_embed(ctx, ctx.arg_str)
            if fetch_embed is None:
                return
            name, embed = fetch_embed
            ctx.objs["embed_preview_msg"] = await ctx.reply("Preview:", embed=embed)
            ctx.objs["embed_embed"] = embed
            ctx.objs["embed_name"] = name

        await ctx.outer_menu(
            [item[0] for item in root_menu],
            root_callback,
            title="Embed Editor",
            prompt="Please type the number of your selection:",
        )


@cmds.cmd("embedinto", category="ServerAdmin", short_help="Embed a stored embed into a message")
@cmds.require("in_server")
@cmds.require("in_server_has_mod")
async def cmd_embedinto(ctx):
    """
    Usage:
        {prefix}embedinto <msgid> [embedname]
    Description:
        Embeds the given embed into the given message.
        This may also be used to edit an embed in a previous message.
        If no embed name is given, will do an interactive lookup.
    """
    if ctx.arg_str == "":
        await ctx.reply("Please supply the message id to embed into.")
        return

    fetch_embed = await get_server_embed(ctx, ctx.arg_str[len(ctx.params[0]) :].strip() if len(ctx.params) > 1 else "")
    if fetch_embed is None:
        return

    out_msg = await ctx.reply(
        "Searching for message, please wait {}".format(ctx.aemoji_mention(ctx.bot.objects["emoji_loading"])),
    )

    message = await ctx.find_message(ctx.params[0])
    if not message:
        await ctx.bot.edit_message(out_msg, "No message with this id found!")
    elif message.author != ctx.me:
        await ctx.bot.edit_message(out_msg, "I can't embed into someone else's message!")
    else:
        try:
            await ctx.bot.edit_message(message, embed=fetch_embed[1])
            await ctx.bot.edit_message(out_msg, "Successfully embedded into the message!")
        except Exception:
            await ctx.bot.edit_message(out_msg, "An unknown error occurred while embedding!")


@cmds.cmd("embed", category="Utility", short_help="View an embed created with the Embed Editor")
@cmds.require("in_server")
async def cmd_embed(ctx):
    """
    Usage:
        {prefix}embed [embedname]
    Description:
        Displays an embed created with the embed editor.
        If no name is given, and there is more than one available embed, supplies a list of the server embeds.
    """
    fetch_embed = await get_server_embed(ctx, ctx.arg_str)
    if fetch_embed is None:
        return
    await ctx.offer_delete(await ctx.reply(embed=fetch_embed[1]))


def load_into(bot):
    bot.data.servers_long.ensure_exists("server_embeds", shared=True)
