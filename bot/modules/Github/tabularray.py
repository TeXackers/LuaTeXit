import github
from github import Auth, Github
from github.ContentFile import ContentFile

from .GithubColours import GithubColour
from .GithubLayouts import GithubEmbed
from .module import github_module as module
from .util import _gh_pagination, _syntax_selection, grab_image, sanitise_image

"""
Provides a quick and easy way to display github issues and pull requests for `tabularray` from Github.

"""

# General ideas
# ;tblr <num>: Displays the issue/PR of the given number. (Github redirects, so only the number is needed.)
# ;tblr issue <text>: List issues containing the given text.


@module.cmd(
    name="tabularray",
    desc="Displays Github-related information about `tabularray` repository.",
    aliases=["tblr"],
    flags=["file", "list"],
)
async def cmd_tabularray(ctx, flags):
    """
    Usage``:
        {prefix}tblr <issue/PR number>
        {prefix}tblr --file [filename] (tabularray-dev.sty if none)
        {prefix}tblr --list [directory] (root if none)
    Description:
        Query issues or PRs of the `tabularray` repository by their number, or list the contents of a file/directory in the repository. For file/directory queries, the `dev-version` branch is used.
    Examples:
        {prefix}tblr 664
        {prefix}tblr --file tabularray-dev.sty
        {prefix}tblr --list doc
    """
    GITHUB_TOKEN: str = ctx.client.conf["GITHUB_AUTH_TOKEN"]
    __github_api = Github(auth=Auth.Token(GITHUB_TOKEN), lazy=True)
    __texackers = __github_api.get_organization("TeXackers")
    __tabularray = __texackers.get_repo("tabularray")

    out_msg = await ctx.reply(
        "Querying Github, please wait... {}".format(
            ctx.client.conf.emojis.getemoji("loading")
        )
    )
    # no flags provided, treat the argument as either an issue/PR number or a search query
    if not flags["file"] and not flags["list"]:
        query = ctx.args.strip()
        if (not query.isdigit()) or (int(query) > 10000) or (len(query) > 10):
            await out_msg.delete()
            return await ctx.error_reply(
                "Please provide a valid issue/PR number or a search query"
            )

        _gh_issue_num = int(query)
        try:
            _issue = __tabularray.get_issue(_gh_issue_num)
            try:
                __test_title = _issue.title
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
                    f"Could not find issue/PR #{_gh_issue_num}, because {reason}"
                )

            # change embed colour based on the state of the issue/PR
            match _issue.state, _issue.state_reason:
                case "open", _:
                    _embed_colour = GithubColour.github_green
                    _state_msg = "Open"
                case "closed", "completed":
                    _embed_colour = GithubColour.copilot_purple
                    _state_msg = "Completed"
                case "closed", "not_planned":
                    _embed_colour = GithubColour.primary.grey4
                    _state_msg = "Not Planned"
                case "open", "reopened":
                    _embed_colour = GithubColour.primary.green4
                    _state_msg = "Reopened"
                case _, _:
                    _embed_colour = GithubColour.security_blue
                    _state_msg = "Unknown State"

            # do image-sanitisation and thumbnail grabbing concurrently
            _sanitised_body = (
                await sanitise_image(_issue.body)
                if _issue.body
                else "No description provided."
            )
            _thumbnail_url = await grab_image(_issue.body) if _issue.body else None

            await out_msg.delete()
            return await ctx.reply(
                view=GithubEmbed(
                    title=f"{'Issue' if not _issue.pull_request else 'Pull Request'} #{_issue.number}: {_issue.title}",
                    url=_issue.html_url,
                    description=_sanitised_body[:2000],
                    colour=_embed_colour,
                    author={
                        "name": _issue.user.login,
                        "url": _issue.user.html_url,
                        "icon_url": f"https://avatars.githubusercontent.com/u/{_issue.user.id}?v=4",
                    },
                    footer_text=f"Status: {_state_msg}",
                    images=_thumbnail_url if _thumbnail_url else None,
                )
            )
            # gh_embed = discord.Embed(
            #     title=f"{'Issue' if not _issue.pull_request else 'Pull Request'} #{_issue.number}: {_issue.title}",
            #     url=_issue.html_url,
            #     description=_issue.body[:2000],
            #     color=_embed_colour,
            # )
            # gh_embed.set_author(
            #     name=_issue.user.login,
            #     url=_issue.user.html_url,
            #     icon_url="https://avatars.githubusercontent.com/u/{}?v=4".format(_issue.user.id),
            # )
            # gh_embed.set_footer(
            #     text=f"Status: {_state_msg}",
            # )
            # return await out_msg.edit(content="", embed=gh_embed)
        except github.UnknownObjectException:
            await out_msg.delete()
            return await ctx.error_reply(
                f"Something went wrong while fetching the issue/PR #{_gh_issue_num}. Please try again later."
            )

    elif flags["file"]:
        query = ctx.args.strip()
        # if query is empty, display the tabularray-dev.sty file in dev-version branch
        if query == "":
            try:
                __file_cf: ContentFile = __tabularray.get_contents(
                    "tabularray-dev.sty", ref="dev-version"
                )
                __file_content: str = __file_cf.decoded_content.decode("utf-8")
            except github.UnknownObjectException as e:
                match e.status:
                    case 302:
                        reason = "it has been moved permanently [302]."
                    case 304:
                        reason = (
                            "it has not been modified since the last request [304]."
                        )
                    case 403:
                        reason = "access to the file is forbidden [403]."
                    case 404:
                        reason = "it does not exist [404]."
                    case _:
                        reason = "an undocumented (by GitHub) error occurred [Unknown Status Code: {}].".format(
                            e.status
                        )
                await out_msg.delete()
                return await ctx.error_reply(
                    f"Could not find the requested file, because {reason}"
                )

            embeds = await _gh_pagination(
                __file_content,
                "tabularray-dev.sty",
                "Content of the `tabularray-dev.sty` file in the `dev-version` branch.",
                syntax=_syntax_selection("tabularray-dev.sty"),
            )

        # hopefully here query isn't empty
        else:
            __file_cf: ContentFile = __tabularray.get_contents(query, ref="dev-version")

            try:
                __file_content: str = __file_cf.decoded_content.decode("utf-8")
            except github.UnknownObjectException as e:
                match e.status:
                    case 302:
                        reason = "it has been moved permanently [302]."
                    case 304:
                        reason = (
                            "it has not been modified since the last request [304]."
                        )
                    case 403:
                        reason = "access to the file is forbidden [403]."
                    case 404:
                        reason = "it does not exist [404]."
                    case _:
                        reason = "an undocumented (by GitHub) error occurred [Unknown Status Code: {}].".format(
                            e.status
                        )
                await out_msg.delete()
                return await ctx.error_reply(
                    f"Could not find the requested file, because {reason}"
                )

            embeds = await _gh_pagination(
                "Content View",
                query,
                "Content of the `{}` file in the `dev-version` branch.".format(query),
                syntax=_syntax_selection(query),
            )
        await out_msg.delete()
        return await ctx.pager(embeds, locked=False)

    elif flags["list"]:
        # list all directories and files in the root of the repository
        query = ctx.args.strip()
        if query == "":
            # assume dev-version
            __contents: list[ContentFile] = __tabularray.get_contents(
                "", ref="dev-version"
            )

            # make a `ls -laH` style listing
            listing = ""
            for content in __contents:
                if content.type == "dir":
                    listing += "📁 `{}/`\n".format(content.path)
                elif content.type == "file":
                    listing += "📄 `{}`\n".format(content.path)
                else:
                    listing += "❓ `{}`\n".format(content.path)

            return await out_msg.edit(
                content=f"Listing of the root directory of the `dev-version` branch:\n\n{listing}"
            )

        else:
            try:
                __contents: list[ContentFile] = __tabularray.get_contents(
                    query, ref="dev-version"
                )
            except github.GithubException as e:
                match e.status:
                    case 302:
                        reason = "it has been moved permanently [302]."
                    case 304:
                        reason = (
                            "it has not been modified since the last request [304]."
                        )
                    case 403:
                        reason = "access to the file is forbidden [403]."
                    case 404:
                        reason = "it does not exist [404]."
                    case _:
                        reason = "of an undocumented (by GitHub) error [Unknown Status Code: {}].".format(
                            e.status
                        )
                await out_msg.delete()
                return await ctx.error_reply(
                    f"Could not find the requested file/directory, because {reason}"
                )

            # make a `ls -laH` style listing
            listing = ""
            for content in __contents:
                if content.type == "dir":
                    listing += "📁 `{}/`\n".format(content.path)
                elif content.type == "file":
                    listing += "📄 `{}`\n".format(content.path)
                else:
                    listing += "❓ `{}`\n".format(content.path)

            return await out_msg.edit(
                content=f"Listing of the {query} directory of the `dev-version` branch:\n\n{listing}"
            )
