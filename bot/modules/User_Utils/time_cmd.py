import itertools
import random
from datetime import datetime

import discord
from cmdClient import Context
from cmdClient.Layouts import Body, Footer, Header
from constants import LuaTeXitCC
from discord.ui import Container, LayoutView, MediaGallery, Separator
from pytz import all_timezones, timezone

from .countrymap import countries
from .module import utils_module as module
from .swiss_clock import SECONDARY_HAND_NAME, render_swiss_clock

"""
Provides a time command for setting user timezone and displaying time.

Commands provided:
    time:
        Display the author or another user's time, and interactively set timezone.
User data:
    tz: string (valid timezone)
        (app independent, user configured)
        The user's timezone in pytz format.
"""

# Some quotes about time
time_quotes: list[str] = [
    '"Men talk of killing time, while time quietly kills them." -- Dion Boucicault',
    '"Time brings all things to pass." -- Aeschylus',
    '"Time is a storm in which we are all lost." -- William Carlos Williams',
    '"The trouble is, you think you have time." -- Jack Kornfield',
    '"The only reason for time is so that everything doesn\'t happen at once." -- Albert Einstein',
    '"Who controls the past, controls the future: who controls the present controls the past." -- George Orwell',
    '"They always say time changes things, but you actually have to change them yourself." -- Andy Warhol',
    '"There\'s never enough time to do all the nothing you want." -- Bill Watterson',
    '"It\'s not that we have little time, but more that we waste a good deal of it." -- Seneca',
]

# Generate list of countries per continent and the continent name list
cont_dict: dict[str, list] = {}
for country in countries:
    if country["continent"] not in cont_dict:
        cont_dict[country["continent"]] = [country]
    else:
        cont_dict[country["continent"]].append(country)
continents: list[dict] = [{"name": name, "countries": countries} for name, countries in cont_dict.items()]
cont_names: list[str] = [c["name"] for c in continents]


def get_time(tz: str) -> datetime:
    """
    Get a datetime object representing the current time in the given timezone.
    """
    return datetime.now(timezone(tz))


def gen_tz_strings(tzlist: list[str]) -> list[str]:
    """
    Generates blocks of timezone (time) pairs with nice spacing, ready for use in a pager.
    """
    formatted_tzlist: list[tuple[str, str]] = [(tz, get_time(tz).strftime("%H:%M")) for tz in tzlist]
    tz_blocks: list[list[tuple[str, str]]] = [formatted_tzlist[i : i + 20] for i in range(0, len(formatted_tzlist), 20)]
    max_block_lens: list[int] = [len(max(next(zip(*tz_block, strict=True)), key=len)) for tz_block in tz_blocks]
    # find the longest string in each block, and use that to format the output nicely
    block_strs: list[list[str]] = [
        ["{0[0]:<{max_len}} {0[1]:<10}".format(tzpair, max_len=max_block_lens[i]) for tzpair in tzblock]
        for i, tzblock in enumerate(tz_blocks)
    ]
    return list(itertools.chain(*block_strs))


async def tz_lookup(ctx: Context, search_str: str) -> str | None:
    """
    Intelligently Lookup a timezone from a given partial or full string.
    """
    # If the search string already has a valid timezone, great
    if search_str in all_timezones:
        return search_str

    search_str = search_str.lower()
    # Generate timezone list for searching
    searchlist = [
        (tz, "{} {} {}".format(tz, get_time(tz).strftime("%I:%M%p"), get_time(tz).strftime("%H:%M")).lower())
        for tz in all_timezones
    ]

    options = []
    if ":" in search_str:
        # If it has a colon it's probably a time
        search_str = search_str.replace(" ", "")

        # Look for this time in the search list
        options = [tz for tz, tzstr in searchlist if search_str in tzstr]
        if not options:
            # Time not found. Try to get the last digit and increase it by one, then look again.
            if search_str[-1].isdigit():
                search_str = search_str[:-1] + str(int(search_str[-1]) + 1)
                options = [tz for tz, tzstr in searchlist if search_str in tzstr]
            elif search_str[-3].isdigit():
                search_str = search_str[:-3] + str(int(search_str[-3]) + 1) + search_str[-2:]
                options = [tz for tz, tzstr in searchlist if search_str in tzstr]
    else:
        # So it's not a time, just some string.
        search_str = search_str.replace(" ", "_")

        # Look for this in the search list
        options = [tz for tz, tzstr in searchlist if search_str in tzstr]

    if options:
        # Yay we found some matches
        tzid = await ctx.selector(
            "Multiple matching timezones found, please select one!",
            gen_tz_strings(options),
            allow_single=False,
        )
        return options[tzid] or None
    # Nope, we tried our best but couldn't find any matches
    await ctx.error_reply("No matching timezones were found!")
    return None


async def tz_picker(ctx):
    """
    Interactive timezone selector for setting the author's timezone.
    """
    contid = await ctx.selector("Please select your continent.", cont_names)
    if contid is None:
        return None

    countries = continents[contid]["countries"]
    countrynames = [c["name"] for c in countries]
    countryid = await ctx.selector("Please select your country", countrynames)
    if countryid is None:
        return None

    timezones = countries[countryid]["timezones"]
    timezone_strs = gen_tz_strings(timezones)
    tzid = await ctx.selector("Please select your timezone", timezone_strs)

    return timezones[tzid] if tzid is not None else None


def get_timestr(tz, brief=False):
    """
    Get the current time in the given timezone, using a fixed format string.
    """
    format_str = "**%H:%M, %d/%m/%Y**" if brief else "**%I:%M %p (%Z)** on **%a, %d/%m/%Y**"
    return get_time(tz).strftime(format_str)


async def reply_with_clock(ctx: Context, tz: str, auth_tz: str | None, header: str, body: str) -> None:
    """
    Reply with a Swiss railway clock face for `tz`, shown full-size via a MediaGallery.

    If the author has their own timezone set and it differs from `tz`, a second,
    differently-coloured hour hand is added to the same face for the author's time,
    instead of rendering a whole separate clock.
    """
    dt = get_time(tz)
    other_dt = get_time(auth_tz) if auth_tz and auth_tz != tz else None
    buf = render_swiss_clock(dt, other_dt=other_dt)

    footer = f"Requested by {ctx.author}"
    if other_dt:
        footer += f" | {SECONDARY_HAND_NAME}: your time"

    container = Container(accent_colour=LuaTeXitCC["cyan"])
    container.add_item(Header(header, 3))
    container.add_item(Separator())
    container.add_item(Body(body))
    container.add_item(MediaGallery(discord.MediaGalleryItem("attachment://clock.png")))
    container.add_item(Footer(footer))

    view = LayoutView()
    view.add_item(container)
    await ctx.reply(file=discord.File(buf, filename="clock.png"), view=view)


@module.cmd(
    "time",
    desc="Displays the current time for a user",
    flags=["set", "at", "list", "brief", "24h", "reset"],
    aliases=["ti"],
)
async def cmd_time(ctx: Context, flags: dict):
    """
    Usage``:
        {prefix}time [user]
        {prefix}time --set [timezone or time]
        {prefix}time --at <timezone>
        {prefix}time --brief
        {prefix}time --list
        {prefix}time --reset
    Description:
        Shows the current time for yourself or the provided user, alongside a Swiss railway clock face.
        If you're comparing against someone else's time (or your own, via `at`) and you have your own
        timezone set, the clock gets a second, cyan hour hand showing your own time.
        Use the `set` flag to interactively pick your timezone from the international tz database.
        You can also view the time in a particular timezone using the `at` flag.
        The `at` flag also allows you to see a list of timezones with a specific given time.
    Flags::
        at: Shows the current time in the timezone given. (Can be a partial timezone)
        brief: Toggles usage of a briefer time display.
        list: Displays a list of valid timezones in the tz database, as shown [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
        reset: Resets the currently set timezone. This cannot be undone.
        set: Sets your timezone to the one provided, or shows an interactive timezone picker.
    Examples``:
        {prefix}time {ctx.msg.author.name}
        {prefix}time --set
        {prefix}time --set Australia/Melbourne
        {prefix}time --set Australia
        {prefix}time --at Melbourne
        {prefix}time --at 06:00
    """
    prefix = await ctx.best_prefix()

    time_data = ctx.client.data.user_time_settings
    tauthor = time_data.select_where(userid=ctx.author.id)
    brief = tauthor[0]["brief_display"] if tauthor else False
    auth_tz = tauthor[0]["timezone"] if tauthor else None

    if flags["set"]:
        # Handling setting a timezone
        # Grab the timezone from interactive lookup if args are given, otherwise the interactive picker
        tz = (await tz_lookup(ctx, ctx.args)) if ctx.args else (await tz_picker(ctx))

        if tz:
            # We have a timezone, display the success message, current time, and a warning about Etc if needed.
            user_time = get_timestr(tz, brief=brief)
            msg = f"Your timezone has been set to `{tz}`!\nYour current time is {user_time}."
            if ctx.args and tz.startswith(("Etc/GMT+", "Etc/GMT-")):
                other_tz = tz.replace("+", "-").replace("-", "+")
                other_time = get_timestr(other_tz, brief=brief)
                proper_time = other_tz[4:]
                warning = (
                    f"\nNote that due to the POSIX standard, the timezone `{tz}` represents the time in `{proper_time}`.\n"
                    f"If your time is incorrect, consider setting your timezone to `{other_tz}`, "
                    f"where the time is currently {other_time}.\n"
                    "You can read more about the standard at https://en.wikipedia.org/wiki/Tz_database#Area."
                )

                msg += warning

            time_data.upsert(constraint="userid", userid=ctx.author.id, timezone=tz)
            await ctx.reply(msg)
        else:
            # We failed to get a timezone, post setting help.
            setter_help = "Need help setting your timezone? One of the following might help!"
            methods = []
            if ctx.args:
                methods.append("Try using our interactive timezone picker with `{prefix}ti --set`")
            else:
                methods.append(
                    "Try entering the name of your nearest capital city, e.g. `{prefix}ti --set London`, "
                    "or your current time, e.g. `{prefix}ti --set 7:20`.",
                )
            methods.append("Find your timezone in the complete list with `{prefix}ti --list`")
            methods.append(
                "Use [this interactive map](http://kevalbhatt.github.io/timezone-picker) to find your timezone!",
            )
            methods.append(
                "Get your timezone from your country and region "
                "[here](http://www.timezoneconverter.com/cgi-bin/findzone)!",
            )
            methods.append("Or join our [support server]({support}) and ask one of our friendly support team!")

            desc = ("\n".join(methods)).format(prefix=prefix, support=ctx.client.app_info["support_guild"])
            embed = discord.Embed(title=setter_help, description=desc, colour=discord.Colour.green())
            await ctx.reply(embed=embed)
    elif flags["at"]:
        # Handle getting the time at a given timezone
        if not ctx.args:
            # No timezone was given, grumble and return
            # TODO: adapt interactive picker for this
            await ctx.reply(f"Usage: `{prefix}ti --at <timezone>`, e.g. `{prefix}ti --at Melbourne`")
        else:
            # Lookup the timezone
            tz = await tz_lookup(ctx, ctx.args)
            if not tz:
                # Timezone lookup failed, the lookup will have already grumbled so just pass on
                pass
            else:
                body = get_timestr(tz, brief=brief)
                await reply_with_clock(ctx, tz, auth_tz, header=f"Time in `{tz}`", body=body)
    elif flags["list"]:
        tzl: list[tuple[str, str]] = [(tz, get_time(tz).strftime("%H:%M")) for tz in all_timezones]
        max_len = len(max(next(zip(*tzl, strict=True)), key=len))
        await ctx.pager_v2(
            "\n".join([f"{tz:<{max_len}} | {time}" for tz, time in tzl]),
            title="Timezone list",
            code=True,
            maxheight=30,
        )
    elif flags["brief"]:
        brief = 1 - brief
        time_data.upsert(constraint="userid", userid=ctx.author.id, brief_display=bool(brief))
        await ctx.reply("Your clock is now more compact." if brief else "Your clock is now more verbose.")
    elif flags["reset"]:
        # Add a confirmation before resetting the timezone
        if await ctx.ask("Are you sure you want to reset your timezone?"):
            # Reset the timezone of the author
            time_data.upsert(constraint="userid", userid=ctx.author.id, timezone=None)
            await ctx.reply("Your timezone has been reset.")
        else:
            await ctx.reply("Question cancelled. Your timezone has not been reset.")

    else:
        # All flags have been handled, all that remains is time reporting for targeted user or author.

        # Find the user
        if not ctx.guild:
            user = ctx.author
        # Consider Message references for selecting a user
        elif ctx.msg.reference:
            if ctx.msg.reference.resolved:
                user = await ctx.find_member(str(ctx.msg.reference.resolved.author.id))
                if not user:
                    return
            else:
                return
        else:
            user = (await ctx.find_member(ctx.args, interactive=True)) if ctx.args else ctx.author
        if not user:
            # Failed to find the target user
            # find_member already complained, so just return
            return
        # Found a user, get their timezone and construct the time message
        tuser = time_data.select_where(userid=user.id)
        tz = tuser[0]["timezone"] if tuser else None

        if not tz:
            # Oops, this user doesn't have a timezone set.
            if user == ctx.author:
                msg = (
                    "You haven't set your timezone! "
                    "Set it using the interactive timezone picker with `{prefix}ti --set`."
                )
            elif ctx.guild and user == ctx.guild.me:
                msg = random.choice(time_quotes)
            else:
                msg = "This user hasn't set their timezone! Ask them to set it using `{prefix}ti --set`."
            await ctx.reply(msg.format(prefix=prefix))
        else:
            body = get_timestr(tz, brief=brief)
            await reply_with_clock(ctx, tz, auth_tz, header=f"{user.display_name}'s time", body=body)
