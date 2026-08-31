# SETUP — Deployment Runbook (go-live day)

Ordered checklist. Everything before §4 happens on YOUR machine; §4 onward on his.
On Windows, replace `python3` with `python` (or `py`) in every command.

## 1. Prepare the repo (your machine, ~30 min)

- [ ] Unzip / clone this repo.
- [ ] `curriculum/projects.md` — replace every `[FILL]` with real channel/series
      names for P1–P6. **The system does not work with placeholders**; the whole
      design is that he ships into your actual channels.
- [ ] `state/progress.json` — his name, start date (his day 1).
- [ ] Drop starter material:
      - `projects/P1/episode/` — the published episode he will re-master (video
        + separate narration track if you have it).
      - `projects/P1/drill_clips/` — 20 assorted clips for the T002 keyboard drill.
- [ ] Optional: skim `state/backlog.json` and add `"due"` dates to T001–T003
      yourself so the daemon has deadlines from day one (else the agent
      negotiates them at briefing).
- [ ] `git init && git add -A && git commit -m "init"` and push to a **private**
      remote. The agent auto-commits each session; the remote is your backup
      and audit trail.

## 2. Discord (~15 min)

- [ ] Create a private server (or channel) with just you and him.
- [ ] Channel → Integrations → Webhooks → New → copy URL.
- [ ] Discord Settings → Advanced → Developer Mode ON. Right-click each of you
      → Copy User ID.
- [ ] `cp config/daemon.example.json config/daemon.json`, paste webhook URL and
      both IDs, set `briefing_time` to when his day starts.
- [ ] For slash commands (`/dev`, `/status`, `/report`):
      - discord.com/developers → New Application → Bot → copy token into
        `config/daemon.json` (`bot_token`).
      - OAuth2 → URL Generator → scopes `bot` + `applications.commands` →
        open the URL, invite to your server.
- [ ] `config/daemon.json` is gitignored — copy it to his machine manually.

## 3. His machine — prerequisites (~30 min)

- [ ] Python 3.10+ installed and on PATH (`python3 --version`).
- [ ] ffmpeg installed and on PATH (`ffmpeg -version`).
- [ ] Premiere Pro installed and licensed.
- [ ] Claude Code installed and **logged in** (`claude --version`, then run
      `claude` once interactively to complete auth). Remote `/dev` runs use his
      login, so the machine must stay on for remote access to work.
- [ ] `pip install discord.py` (only needed for slash commands).
- [ ] Git installed; clone the private repo; copy `config/daemon.json` in.

## 4. Verify (5 commands, in the repo root on his machine)

```bash
python3 tools/new_day.py            # JSON block, next task T001, daemon_running false
python3 tools/ensure_daemon.py      # {"action": "started", "running": true, ...}
python3 tools/new_day.py            # daemon_running should now be true
python3 tools/validate_asset.py library/  2>/dev/null; echo ok   # tool runs
tail -n 20 logs/daemon.log          # heartbeat lines; "bot ready" if token set
```

Then in Discord: you should see nothing yet (digest waits for `briefing_time`).
Test the loop end-to-end: type `/status` — a short digest should come back.
Type `/dev say hello and confirm you can read state/backlog.json` — the reply
should quote task T001. If both work, the remote loop is live.

## 5. Session 1 — sit with him (60–90 min, once)

1. He opens the repo in Claude Code and types: **"what should I do today?"**
2. Watch the loop run once: standup → T001 briefed with acceptance criteria →
   he works → "done" → the agent collects the result log → validators run →
   scores → Discord posts the ✅ tagging you.
3. Make him do the result log himself — the gate only teaches if he feels it.
4. Before you leave, queue tomorrow's encouragement: in the same chat type
   `it's the dev — queue a directive welcoming him to week 1 and reminding him
   the first week is about hands, not taste.`

## 6. Your weekly operating rhythm (after day 1)

- **~15 min/day, from anywhere:** read the Discord feed; `/status` if curious;
  `/dev …` to adjust priorities, add tasks, answer his blockers.
- **Friday:** the daemon posts the detailed KB report; read `dev/flags.md` via
  `/dev show me dev/flags.md`, then do the review conversation with him
  (in person or call — the numbers are in the report, the coaching is yours).
- **Phase gates (end of P1, P4, P6):** full assessment + belt decision. The
  rubric and evidence are in `logs/weekly/` and `kb/query.py summary`.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `daemon_running` stays false | `python3 daemon/ustaad_daemon.py` in the foreground and read the error; usually a malformed `config/daemon.json` |
| No Discord messages, log says `[discord:disabled]` | `webhook_url` empty/wrong in config |
| Slash commands missing in Discord | bot not invited with `applications.commands`, wrong token, or `discord.py` not installed — check `logs/daemon.log` |
| `/dev` says CLI not found | `claude` not on PATH for the daemon's environment — reinstall Claude Code or set full path in `claude_cmd` |
| `/dev` hangs then times out | headless run hit a tool it isn't allowed to use — widen `claude_extra_args` in config |
| Agent skips the result-log gate | it must run `tools/new_day.py` first; if it didn't, tell it to re-read `CLAUDE.md` |
| Double digests / duplicate pings | delete `state/notify_state.json` once; it rebuilds |
| Fresh machine / moved repo | delete `state/daemon_heartbeat` + `state/daemon.pid`, re-run `ensure_daemon.py` |

## 8. Day-2+ hygiene (set and forget)

- The agent commits every session; check the remote weekly so backups are real.
- `logs/sessions.jsonl` is the one file that must never be lost — everything
  else (including the knowledge graph) rebuilds from it.
- When the backlog runs low the agent generates the next arc itself; steer it
  any time with `/dev` (e.g. `/dev bias the next task batch toward sound
  design and set due dates one day tighter`).
