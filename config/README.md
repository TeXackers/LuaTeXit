# Configuration

This README documents how the bot is configured via its `.conf` file(s). The format is `ini`-like, parsed by [`bot/config.py`](../bot/config.py) using Python's [`configparser`](https://docs.python.org/3/library/configparser.html). See [`example-bot.conf`](example-bot.conf) for a template.

## How to start the bot

To start the bot,

1. Clone the repo and cd into it
2. Install dependencies via `python -m pip install -r requirements.txt`
3. Fill out the config so the bot can run. A template is in the config folder (you can name it `<whatever>.conf`)
4. Run `python bot/main.py --createdb`
5. Run `python bot/main.py --writeschema data/schemas/sqlite_schema.sql`
6. The bot should be good to go, run `python bot/main.py`. To run it on a baremetal machine, I like using `python bot/main.py 2>&1 & disown`.

N.B. you can pass `--conf <path>` (`bot/paraArgs.py`) to point at a different file, otherwise it defaults to `config/paradox.conf`.

## File structure

```
[DEFAULT]
key = value
...

[SHARD <n>]
key = value          ; overrides DEFAULT for that shard only

[EMOJIS]
name: <emoji-literal>
```

### `[DEFAULT]`

holds every base setting. Any key here is visible from every other section (`configparser` fallback behaviour).

### `[SHARD <n>]` (e.g. `[SHARD 0]`)

overrides `DEFAULT` for the shard started with `--shard <n>`. Only override what differs per shard, everything else falls through.

### `[EMOJIS]`

Old way of mapping logical emoji names used by the bot to literal Discord emoji strings. It uses `:` instead of `=` as the separator (both are valid `configparser` delimiters though), purely by convention in this file.

### Additional notes

- Keys are **case-insensitive** because para's `configparser` lowercases them internally i.e. `TOKEN`, `Token` and `token` are equivalent.
- Lines starting with `#` are comments.
- A key can pull in another file wholesale via `ALSO_READ` (see [Field reference](#field-reference)).

## Value types

Every field below is typed according to how it's read back out of the config (see the `converters` in `bot/config.py`).
N.B. Whitespace around values is stripped.

```bnf
<string>    ::= <any text up to end of line>
<int>       ::= ["-"] <digit>+
<digit>     ::= "0" | "1" | ... | "9"
<snowflake> ::= <int>                        ; a Discord ID (channel/user/guild)
<bool>      ::= "1" | "yes" | "true"  | "on"
              | "0" | "no"  | "false" | "off"   ; configparser getboolean(), case-insensitive
<path>      ::= <string>                     ; filesystem path, relative to cwd unless absolute

<list>      ::= <item> ("," <item>)*
<item>      ::= <string without a comma>     ; each item is stripped of surrounding whitespace
<intlist>   ::= <int> ("," <int>)*
<snowlist>  ::= <snowflake> ("," <snowflake>)*   ; intlist of Discord IDs

<emoji>     ::= "<" ["a"] ":" <name> ":" <snowflake> ">" [" or " <fallback>]
<name>      ::= <string without ":">
<fallback>  ::= <string>                     ; e.g. a plain unicode emoji, used if the
                                             ; custom emoji can't be resolved
```

Generally, `<list>`/`<intlist>` are read with `conf.getlist(key, default)` / `conf.getintlist(key, default)` and
`<emoji>` is read with `conf.emojis.getemoji(name)`.

## Field reference

### `[DEFAULT]` / `[SHARD <n>]`

| Key | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `token` | `<string>` | REQUIRED | Discord bot token.**Secret** |
| `prefix` | `<string>` | `~` | Default command prefix. |
| `app` | `<string>` | `paradox` | Which app config to load. You can make your own in [`bot/apps/`](../bot/apps/) |
| `shard_count` | `<int>` | `1` | Total number of shards the bot is running as. |
| `also_read` | `<list<path>>` | `[]` | Additional config file(s) to read in, applied after this file. Processed recursively (each included file's own `also_read` is also followed). |
| `masters` | `<snowlist>` | `[]` | User IDs with full bot-owner control. |
| `developers` | `<snowlist>` | `[]` | User IDs with developer-level access. |
| `managers` | `<snowlist>` | `[]` | User IDs who can moderate/manage bot content (e.g. approve preambles). |
| `reviewers` | `<snowlist>` | `[]` | User IDs who can review submitted content. |
| `whitelisted_bots` | `<snowlist>` | `[]` | Bot user IDs allowed to trigger commands (bots are ignored otherwise). |
| `blacklisted_users` | `<snowlist>` | `[]` | User IDs blocked from interacting with the bot. |
| `blacklisted_guilds` | `<snowlist>` | `[]` | Guild IDs where the bot won't process bot-author messages. |
| `logfile` | `<path>` | REQUIRED | Path to the bot's rotating log file. |
| `loglevel` | `<string>` | `INFO` | Log level for the bot logger. `DEBUG` will show extra. |
| `discord_loglevel` | `<string>` | `INFO` | Log level for the underlying`discord.py` logger. |
| `db_type` | `"sqlite"` | `sqlite` | Storage backend.`sqlite` is the only supported/working option — see note below. |
| `sqlite_db` | `<path>` | `data/paradox.db` | Sqlite database file. |
| `feedback_ch` | `<snowflake>` | REQUIRED | Channel where`/feedback` submissions are posted. |
| `preamble_ch` | `<snowflake>` | REQUIRED | Channel for preamble submissions. |
| `preamble_logch` | `<snowflake>` | - | Channel preamble actions are logged to. |
| `preamble_subch` | `<snowflake>` | - | Channel preamble submissions are sent to for review. |
| `guild_log_ch` | `<snowflake>` | REQUIRED | Channel for guild join/leave logging. |
| `log_channel` | `<snowflake>` | REQUIRED | General-purpose bot log channel. |
| `error_channel` | `<snowflake>` | falls back to `log_channel` | Channel unhandled errors are reported to. |
| `wolfram_id` | `<string>` | - | Wolfram\|Alpha App ID, used by the `wolf` command. |
| `kagi_id` | `<string>` | - | Kagi API key. **Secret** |
| `github_auth_token` | `<string>` | REQUIRED | GitHub personal access token used for GitHub API lookups. **Secret** |

Fields marked "required" will cause a startup error (or silently misbehave, e.g. `None` channel
IDs) if left unset - always set them, even in a dev config.

### `[EMOJIS]`

**This is an OLD way of mapping emojis used by the bot. You should instead add them on Application Emoji under Discord Developer Portal (e.g., `https://discord.com/developers/applications/<application_id>/emojis`) then load with [`ctx.client.fetch_application_emojis()`](https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.fetch_application_emojis)**

Each key names a logical emoji slot the bot code looks up via `conf.emojis.getemoji("<name>")` ([`bot/paraEmoji.py`](../bot/paraEmoji.py)); the value is an `<emoji>` literal, i.e. Discord's own `<:name:id>` / `<a:name:id>` format, optionally with `or <fallback>` appended for a plain-unicode fallback if the custom emoji is unavailable.

```
loading: <a:loading:531888356167254036>
prev:    <:Previous:441781666206187520> or ◀
```

Current slots in use: `latex_show_source`, `latex_show_errors`, `latex_delete_source`, `bot`, `botowner`, `botmanager`, `online`, `idle`, `dnd`, `offline`, `next`, `more`, `delete`, `loading`, `prev`, `approve`, `deny`, `test`, `sendfile`. Some call sites (e.g. `cancel`) pass their own in-code fallback and don't require the key to be present at all.

## Notes

- `*.conf` is gitignored: `paradox.conf` is expected to hold real secrets and should never be committed. Use `example-bot.conf` as the template for a new deployment.
- Values are read with `str.strip()`, so trailing whitespace/comments on the same line are safe, but inline `# comment` after a value is **not** stripped by `configparser`, so keep comments on their own line.
- MySQL is not currently usable so stick to `db_type = sqlite` until that's fixed.
