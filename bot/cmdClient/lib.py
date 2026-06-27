import re


class SafeCancellation(Exception):
    default_msg: str | None = None

    def __init__(self, msg=None):
        self.msg: str | None = msg or self.default_msg


class UserCancelled(SafeCancellation):
    default_msg = "User cancelled the session!"


class ResponseTimedOut(SafeCancellation):
    default_msg = "Session timed out waiting for user response!"


class InvalidContext(Exception):
    """
    Throw when the context available doesn't match the context expected.
    """

    pass


def sterilise_content(content: str) -> str:
    """
    Sterilse everyone and here mentions in the provided string.
    Specifically, adds a zero width space after the `@` symbol
    when such a ping is detected.

    Parameters
    ----------
    content: str
        String to sterilise

    Returns: str
        Sterilsed string.
    """
    nbsp = "\u200b"
    content = content.replace("@everyone", f"@{nbsp}everyone")
    content = content.replace("@here", f"@{nbsp}here")
    asciimsg = content.encode("ascii", errors="ignore").decode()
    if "@everyone" in asciimsg or "@here" in asciimsg:
        content = content.replace("@", f"@{nbsp}")

    return content


def flag_parser(args: str, flags: list[str] = []) -> tuple[dict[str, str | bool], str]:
    """
    Parses flags in args from the flags given in flags.
    Flag formats:
        'a': boolean flag, checks if present.
        'a=': Eats one "word"
        'a==': Eats all words up until next flag
    Returns a tuple (flag_values, remaining).
    flags_present is a dictionary {flag: value} with value being:
        False if a flag isn't present,
        True if a boolean flag is present,
        The value of the flag for a long flag,
    If -- is present in the input as a word, all flags afterwards are ignored.
    """
    # Split across whitespace, keeping the whitespace
    params: list[str] = re.split(r"(\S+)", args)

    final_flags: dict[str, str | bool] = {flag.strip("="): False for flag in flags}
    indexes: list[tuple[int, str]] = []  # Indices in the params list where the flags appear
    end_params: list[str] = []  # The tail of the parameter list, after -- appears

    # Handle appearance of the flag terminator
    try:
        i = params.index("--")
        end_params: list[str] = params[i + 1 :] if i < len(params) - 1 else []
        params: list[str] = params[:i]
    except ValueError:
        pass

    # Build a map of flag prefixes for faster lookup
    flag_map: dict[str, str] = {}
    for flag in flags:
        clean_flag = flag.strip("=")
        for prefix in ["-", "--", "\u2013"]:
            flag_map[prefix + clean_flag] = flag

    # Find the param indices of the flags (single pass)
    for i, param in enumerate(params):
        if param in flag_map:
            indexes.append((i, flag_map[param]))

    # Sort the indicies to ensure we step through the flags in order of appearance
    indexes = sorted(indexes)

    # Build the parameters and flag arguments
    final_params: list[str] = []
    final_params = params[0 : indexes[0][0]] if len(indexes) > 0 else params.copy()

    for i, (index, flag) in enumerate(indexes):
        # Get the parameters between this flag and the next, or the end
        next_index = indexes[i + 1][0] if i + 1 < len(indexes) else len(params)
        flag_params = params[index + 1 : next_index]

        # Split these into flag arguments and final parameters depending on flag type
        clean_flag = flag.strip("=")
        if flag.endswith("=="):
            final_flags[clean_flag] = "".join(flag_params).strip()
        elif flag.endswith("="):
            # Find the first non-whitespace param, if it exists
            j, arg = next(((j, arg) for j, arg in enumerate(flag_params) if arg.strip()), (len(flag_params), None))

            final_flags[clean_flag] = arg or ""

            # If there are any more params, add them to the final bunch
            if j + 1 < len(flag_params):
                final_params.append("".join(flag_params[j + 1 :]).rstrip())
        else:
            final_flags[clean_flag] = True
            final_params.append("".join(flag_params).rstrip())

    # Add any tail parameters
    final_params.extend(end_params)

    # Generate the remaining args
    remaining = "".join(final_params).strip()
    return (final_flags, remaining)
