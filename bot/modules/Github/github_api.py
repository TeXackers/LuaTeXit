"""
Provides a quick and easy way to display github issues and pull requests for LaTeX-related repositories from Github.

"""

import discord

import github
from github import Auth, Github

from .module import github_module as module
from .util import gh_pagination, gh_view_pagination, syntax_selection


ALLOWED_ORGANISATIONS = ("latex3", "texackers")


@module.cmd(name="github", desc="Looks up information about LaTeX-related repositories on GitHub.", aliases=["gh"])
async def cmd_github_latex_lookup(ctx):
    """
    Usage``:
        {prefix}gh <repository>
    Description:
        Looks up information about a LaTeX-related repository on GitHub. Currently queries the following organisations: `latex3`, `texackers`.
    Examples:
        {prefix}gh tagging-project
        {prefix}gh latex3 --issue 123
    """
    GITHUB_TOKEN: str = ctx.client.conf["GITHUB_AUTH_TOKEN"]
    __github_api = Github(auth=Auth.Token(GITHUB_TOKEN), lazy=True)
    __repo: github.Repository.Repository | None = None
    __orgs_scan = [__github_api.get_organization(org) for org in ALLOWED_ORGANISATIONS]

    out_msg = await ctx.reply("Querying Github, please wait... {}".format(ctx.client.conf.emojis.getemoji("loading")))

    for org in __orgs_scan:
        try:
            __repo = org.get_repo(ctx.args.strip())
            __repo.get_contents("README.md")
            break
        except Exception:
            pass

    # check
    try:
        __repo.get_contents("README.md")
    except github.UnknownObjectException as e:
        match e.status:
            case 302:
                (__reason := "it has been moved permanently [302].")
            case 304:
                (__reason := "it has not been modified since the last request [304].")
            case 403:
                (__reason := "access to the file is forbidden [403].")
            case 404:
                (__reason := "it does not exist [404].")
            case _:
                (__reason := "an undocumented (by GitHub) error occurred [Unknown Status Code: {}].".format(e.status))

        await out_msg.delete()
        return await ctx.error_reply(
            f"\n Could not find `{ctx.args.strip()}` in {', '.join(ALLOWED_ORGANISATIONS)}\n\nThis may be because {__reason}\n"
        )

    # if we got here, __repo should be a valid repository object
    await out_msg.delete()
    return await ctx.reply(
        f"Found repository `{__repo.full_name}`. It has {__repo.open_issues_count} open issues and {__repo.get_pulls(state='open').totalCount} open pull requests."
    )
