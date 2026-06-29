import discord
from cmdClient import Context  # noqa
from constants import LuaTeXitCC

from .module import meta_module as module

"""
Commands for users to give feedback on the bot.

Commands provided:
    feedback:
        Sends an embed containing user-submitted feedback to the feedback channel defined in the config.
"""
# TODO: Interactive bug reporting

# TODO: cooldown on feedback


@module.cmd("feedback", desc="Send feedback to my creators")
async def cmd_feedback(ctx: Context):
    """
    Usage``:
        {prefix}feedback <message>
    Description:
        Give feedback on anything regarding the bot, straight to the developers.
        This can be used for suggestions, bug reporting, or general feedback.
        Note that misuse of this command will lead to blacklisting.
    """
    # Get the feedback channel
    feedback_chid = int(ctx.client.conf.get("feedback_ch"))
    if not feedback_chid:
        return await ctx.error_reply("Sorry, I am not configured to accept feedback at this time.")

    # Get the desired feedback
    response = ctx.args
    if not response:
        response = await ctx.input("What message would you like to send? (`c` to cancel)", timeout=240)
        if response.lower() == "c":
            return await ctx.error_reply("Cancelled question.")

    # Build the feedback embed
    embed = discord.Embed(
        title="Feedback", color=LuaTeXitCC["purple"], timestamp=discord.utils.utcnow(), description=response
    )
    embed.set_author(name=f"{ctx.author} ({ctx.author.id})", icon_url=ctx.author.avatar.url)
    embed.set_footer(text=discord.utils.utcnow().strftime("Sent from {}".format(ctx.guild.name if ctx.guild else "DM")))

    # Send a preview and confirm with the user
    preview = await ctx.reply(embed=embed)
    response = await ctx.ask(
        "Are you sure you wish to submit the following feedback to my developers? (`y`/`n`)", use_msg=preview
    )
    await preview.edit(content="")
    if not response:
        return await ctx.error_reply("Cancelled feedback submission.")

    # Mail in the feedback and thank the user
    await ctx.mail(feedback_chid, embed=embed)
    return await ctx.reply("Thank you! Your feedback has been sent.\n-# LuaTeXit maintainer")
