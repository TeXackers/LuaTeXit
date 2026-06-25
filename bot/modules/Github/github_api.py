"""
Provides a quick and easy way to display github issues and pull requests for LaTeX-related repositories from Github.

"""

import discord
import github
from github.Repository import Repository
from cmdClient import Context
from github import Auth, Github

from .GithubColours import GithubColour
from .GithubLayouts import GithubEmbed
from .module import github_module as module
from .util import grab_image, sanitise_image, lang2colour


def is_alnum_with_hyphen(s: str) -> bool:
    # allowed: - and .
    return all(c.isalnum() or c == "-" or c == "." for c in s if c != "/")


@module.cmd(
    name="github",
    desc="Look up issues from repositories on GitHub.",
    aliases=["gh"],
    flags=["issue"],
)
async def cmd_github_lookup(ctx: Context, flags):
    """
    Usage``:
        {prefix}gh <repository>
    Description:
        Looks up information about any public repository on GitHub.
    Example:
        {prefix}gh typst/typst --issue 6767
        {prefix}gh typst --issue 13 (understood as typst/typst)
    """

    # parse args (args is just space, so split)
    # first arg should be <username>/<repository>
    # in case it's not, we can try <arg>/<arg> and see if that works
    # otherwise exit with an error message
    query_issue = flags["issue"]
    if query_issue:
        query = ctx.args.strip().split()
        if len(query) != 2:
            return await ctx.error_reply(
                "Please provide a repository and an issue number to look up. For example, `typst/typst 123`."
            )
        else:
            orgrepo = query[0]
            issue_num = query[1]

            if not issue_num.isdigit():
                return await ctx.error_reply(
                    f"{issue_num} is not a valid issue number. Please provide a valid issue number."
                )
    else:
        query = ctx.args.strip()
        if not query:
            return await ctx.error_reply(
                "Please provide a repository to look up. For example, `typst/typst` or `latex3`."
            )
        else:
            orgrepo = query
            issue_num = None

    # validate org/repo formatting
    match is_alnum_with_hyphen(orgrepo), "/" in orgrepo:
        case True, True:
            # Valid format: <org>/<repo>
            org, reponame = orgrepo.split("/")
        case True, False:
            # if no hyphen then we double up (like typst/typst)
            org = reponame = orgrepo
        case False, True:
            return await ctx.error_reply(
                f"{orgrepo} is not a valid argument. Consider the following format: `{{org|user}}/{{repository}}`."
            )
        case False, False:
            return await ctx.error_reply(
                f"{orgrepo} is not a valid argument. Consider the following format: `{{org|user}}/{{repository}}`."
            )

    # return await ctx.reply(f"Given {org}/{reponame} \#{issue_num}, I would look up the issue and display its information here. This is a placeholder response for now.")

    out_msg = await ctx.reply(
        "Querying Github, please wait... {}".format(
            ctx.client.conf.emojis.getemoji("loading")
        )
    )
    GITHUB_TOKEN: str = ctx.client.conf["GITHUB_AUTH_TOKEN"]
    github_api = Github(auth=Auth.Token(GITHUB_TOKEN), lazy=True)
    repo: Repository = github_api.get_repo(f"{org}/{reponame}")

    try:
        _ = repo.full_name
    except github.UnknownObjectException as e:
        match e.status:
            case 302:
                (reason := "it has been moved permanently [302].")
            case 304:
                (reason := "it has not been modified since the last request [304].")
            case 403:
                (reason := "access to the repository is forbidden [403].")
            case 404:
                (reason := "it does not exist [404].")
            case _:
                (
                    reason
                    := "an undocumented (by GitHub) error occurred [Unknown Status Code: {}].".format(
                        e.status
                    )
                )

        await out_msg.delete()
        return await ctx.error_reply(
            f"\n Could not find `{org}/{reponame}`\n\nThis may be because {reason}\n"
        )

    if not query_issue:
        try:
            repo.get_contents("README.md")
        except github.UnknownObjectException:
            pass

        await out_msg.delete()

        desc_text = f"{repo.description if repo.description else 'No description provided.'}\n\n\n"
        # add fields
        desc_fields: dict[str, str | int] = {
            "licence": repo.license.spdx_id if repo.license else "None",
            "stars": repo.stargazers_count,
            "forks": repo.forks,
            "watches": repo.subscribers_count,
            "issues": repo.open_issues_count,
        }

        # format
        desc_text += "\n".join(f"`{key:>8}:` {value:<}" for key, value in desc_fields.items())

        return await ctx.reply(
            content="",
            view = GithubEmbed(
                title=f"{repo.name}",
                url=repo.html_url,
                description=desc_text,
                colour=lang2colour(repo),
                author={
                    "name": repo.owner.login,
                    "url": repo.owner.html_url,
                    "icon_url": f"https://avatars.githubusercontent.com/u/{repo.owner.id}?v=4",
                },
                created_at=repo.created_at,
                footer_text=f"Last updated: {discord.utils.format_dt(repo.updated_at, 'R')} | Requested by: {ctx.author.display_name}",
                images=None,
            )
        )
    else:
        try:
            issue = repo.get_issue(int(issue_num))
        except github.UnknownObjectException as e:
            reason: str = ""
            match e.status:
                case 301:
                    reason = "it has been moved permanently [304]."
                case 403:
                    reason = "access to the issue/PR is forbidden [403]."
                case 404:
                    reason = "it does not exist [404]."
                case 410:
                    reason = "it has been deleted [410]."
                case 422:
                    reason = (
                        "validation failed, or the endpoint has been spammed [422]."
                    )
                case 503:
                    reason = "GitHub is currently unavailable [503]."
                case _:
                    reason = "an undocumented (by GitHub) error occurred [Unknown Status Code: {}].".format(
                        e.status
                    )
            await out_msg.delete()
            return await ctx.error_reply(
                f"Could not find issue/PR #{issue_num} in {org}/{reponame}, because {reason}"
            )

        match issue.state, issue.state_reason:
            case "open", _:
                _embed_colour = GithubColour.github_green
                _state_msg = "Last updated"
                _last_update = issue.updated_at
            case "closed", "completed":
                _embed_colour = GithubColour.copilot_purple
                _state_msg = "Closed (completed)"
                _last_update = issue.closed_at
            case "closed", "not_planned":
                _embed_colour = GithubColour.primary.grey4
                _state_msg = "Closed (not planned)"
                _last_update = issue.closed_at
            case "closed", None:
                _embed_colour = GithubColour.copilot_purple
                _state_msg = "Merged" if issue.pull_request else "Closed"
                _last_update = issue.closed_at
            case "open", "reopened":
                _embed_colour = GithubColour.primary.green4
                _state_msg = "Reopened"
                _last_update = issue.updated_at
            case _, _:
                _embed_colour = GithubColour.security_blue
                _state_msg = "Unknown"
                _last_update = issue.updated_at

        sanitised_body = (
            await sanitise_image(issue.body)
            if issue.body
            else "No description provided."
        )
        thumbnail_url = await grab_image(issue.body) if issue.body else None

        await out_msg.delete()
        return await ctx.reply(
            reference=ctx.msg,
            view=GithubEmbed(
                title=f"{'Issue' if not issue.pull_request else 'Pull Request'} #{issue.number}: {issue.title}",
                url=issue.html_url,
                description=sanitised_body[:2000] + "..."
                if len(sanitised_body) > 2000
                else sanitised_body,
                colour=_embed_colour,
                author={
                    "name": issue.user.login,
                    "url": issue.user.html_url,
                    "icon_url": f"https://avatars.githubusercontent.com/u/{issue.user.id}?v=4",
                },
                created_at=issue.created_at,
                footer_text=f"{_state_msg} {discord.utils.format_dt(_last_update, 'R')} | Requested by: {ctx.author.display_name}",
                images=thumbnail_url if thumbnail_url else None,
            ),
        )
