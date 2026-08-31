# Daemon & Discord Setup

The daemon is what makes this system exist when nobody is typing. It runs on
**his** machine (that's where the repo, the state, and the Claude Code CLI live).

## 1. Discord setup (~10 minutes)

**Outbound — webhook (required, zero dependencies)**
1. In your Discord server: Server Settings → Integrations → Webhooks → New Webhook.
2. Point it at the channel you both use. Copy the webhook URL.

**Inbound — bot for your slash commands (optional but this is the remote-control part)**
1. https://discord.com/developers/applications → New Application.
2. Bot tab → Reset Token → copy it. This token lets anyone run commands on his
   machine, so treat it like an SSH key.
3. OAuth2 → URL Generator → scopes `bot` + `applications.commands` → invite to
   your server.
4. Enable Developer Mode in Discord (Settings → Advanced), then right-click to
   Copy ID for: your server (guild), your user, and his user.
5. On his machine: `pip install -U discord.py`

**Config**
```bash
cp config/daemon.example.json config/daemon.json
```
Fill `webhook_url`, `bot_token`, `guild_id`, `dev_user_id`, `trainee_user_id`.
`config/daemon.json` is gitignored — it holds secrets, keep it that way.

Test the wiring:
```bash
python3 daemon/ustaad_daemon.py --test    # should post to your channel
python3 daemon/ustaad_daemon.py --once    # one scheduler tick, prints what it does
```

## 2. Starting it

You don't have to. **Ustaad runs `tools/ensure_daemon.py` at the top of every
session**, which checks the PID file, verifies the process is actually alive
(not just that a stale pidfile exists), and relaunches it detached if not. So
the daemon self-heals every time he opens the repo.

Manual control:
```bash
python3 tools/ensure_daemon.py            # start if down
python3 tools/ensure_daemon.py --status   # check only
python3 tools/ensure_daemon.py --restart  # after editing config
```

**Optional boot persistence** so it survives restarts even on days he doesn't
open Claude Code:

*macOS* — `~/Library/LaunchAgents/com.iztraab.ustaad.plist`, keys: `Label`,
`ProgramArguments` = `[/usr/bin/python3, /path/to/ustaad-os/daemon/ustaad_daemon.py]`,
`RunAtLoad` = true, `KeepAlive` = true. Then `launchctl load -w <plist>`.

*Windows* — Task Scheduler → Create Task → Trigger "At log on" → Action:
`pythonw.exe C:\path\to\ustaad-os\daemon\ustaad_daemon.py` → check "Run whether
user is logged on or not".

## 3. What lands in Discord

| Trigger | Message | Tags |
|---|---|---|
| 09:00 weekdays | Daily briefing: today's task, due time, pending count, weakest dimension | both |
| Task validated/rejected | Scores, assets produced, defects, time spent | you |
| 2h before due | Deadline warning | him |
| Overdue | Repeats hourly; from the 3rd ping it also tags you | him, then both |
| No activity by 11:00 | Idle nudge | him |
| Still nothing by 14:00 | Escalation | both |
| Ustaad writes to `dev/flags.md` | Forwarded verbatim | you |
| Saturday 18:00 | Weekly report: validated/rejected counts, assets, rubric trends, defects | you |

Every time is configurable in `config/daemon.json`. Sundays are skipped
throughout. First boot seeds its file tailers to end-of-file, so installing
mid-programme never replays old history.

## 4. Your slash commands (dev-only, gated on your user ID)

| Command | Does |
|---|---|
| `/dev <query>` | Runs your request through the Claude Code CLI in the repo, with `it's the dev` prefixed. This is full remote control — reassign tasks, adjust the rubric, ask for analysis, fix state. |
| `/status` | Short digest: day, belt, open tasks with due times, weakest dimension |
| `/report` | Full report: open + next 5 pending, rubric per dimension, recurring defects |
| `/directive <text>` | Queues guidance shown to him at his next standup as from you |
| `/pause <hours>` | Silences notifications (events still recorded, nothing lost) |
| `/resume` | Un-silences |

`/dev` shells out to whatever is in `claude_cli.command` (default
`["claude", "-p"]`). If your CLI uses different flags for non-interactive mode,
change it there — the daemon reports a clear error rather than hanging if the
binary isn't found.

## 5. Two things worth being deliberate about

**The bot token is remote code execution on his machine.** `/dev` runs an agent
with file-write access to the repo. Keep the token out of git (it already is),
don't paste it in the shared channel, and rotate it if it leaks. If you'd rather
not have that exposure, run with `--no-bot`: you lose slash commands, keep all
notifications.

**Notifications are shared, not surveillance.** Every message goes to a channel
he's in, `logs/remote_dev.jsonl` records your remote queries in his repo, and
the constitution tells Ustaad to show him that log if he asks. That's
deliberate. A system where he can see exactly what's being tracked produces
honest logs; one where he suspects a hidden channel produces defensive ones,
and the whole knowledge graph is only as good as the honesty of its inputs.
