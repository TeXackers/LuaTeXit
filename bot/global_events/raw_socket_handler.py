from pathlib import Path

app = Path.cwd().parts[-1]
pipefile = "/home/paradox/pipe/" + app

existence = Path.exists(Path(pipefile))

cest_une_pipe = None


async def handle_raw_socket(bot, msg):
    if not existence:
        return

    global cest_une_pipe
    if cest_une_pipe is None:
        cest_une_pipe = Path.open(pipefile, "w")
    if isinstance(msg, str):
        cest_une_pipe.write(msg)
        cest_une_pipe.write("\n")


def load_into(bot):
    if existence:
        bot.add_after_event("socket_raw_receive", handle_raw_socket, priority=5)
