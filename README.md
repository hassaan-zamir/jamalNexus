# USTAAD OS — Setup & Operations (for the dev)

An agentic mentor environment. The trainee opens this repo in Claude Code (or any
agent that reads `CLAUDE.md`, runs Python, and edits files), says "what should I
do today?", and the system runs the whole program: daily tasks, coaching,
validation, logging, a knowledge graph, and a curriculum that regenerates itself
indefinitely.

## 1. Install on his machine

1. Prereqs: **python3** (stdlib only for everything except the Discord bot),
   **ffmpeg** on PATH, Premiere Pro, and Claude Code (or equivalent) logged in.
   For dev slash commands: `pip install -U discord.py`.
2. Copy this repo to his machine. Run `git init` inside it — version history of
   state/logs is your audit trail and your backup. Add a private remote and have
   the agent commit at the end of each session (add that one line to CLAUDE.md
   if you want it automatic).
3. Fill every `[FILL]` placeholder:
   - `curriculum/projects.md` — real channel/series names for P1–P6. **This is
     the important one.** The whole design is that he learns by shipping into
     your actual channels.
   - `state/progress.json` — his name, start date.
4. Drop starter material into `projects/P1/` (the episode to re-master, the 20
   drill clips for T002).
5. Discord + daemon: follow `daemon/SETUP.md` (~10 min). Short version:
   `cp config/daemon.example.json config/daemon.json`, fill the webhook URL and
   IDs, then `python3 daemon/ustaad_daemon.py --test`.
6. Sanity check: `python3 tools/new_day.py` should print a JSON block with
   `T001` as next pending task.

## 2. How a day works (his side)

He opens the repo in Claude Code and talks. The agent:
- runs `tools/ensure_daemon.py` first — it has no memory of whether the
  background service is up, so it checks and relaunches it if not,
- runs `tools/new_day.py`, blocks new work until yesterday's result is logged,
- surfaces any guidance you queued,
- briefs one task with acceptance criteria,
- coaches during the work (it will refuse to do the work for him — by design),
- validates output with `tools/validate_asset.py` / `tools/loudness_check.py`,
- scores against the rubric, logs to `logs/`, rebuilds `kb/graph.json`.

## 3. Your side — dev mode

Type **`it's the dev`** in any message. The agent switches to dev interface:
state digest first, then it takes directives (guidance, redirection, task edits,
priority changes) into `dev/directives.md`, surfaced to him at his next standup
as "guidance from Hassaan". All your edits are recorded in `dev/changelog.md`.

**Be clear about what the keyword is:** a role switch, not authentication. He
can read this repo, including this file. That is deliberate — the system works
because it is a shared, transparent contract, and an agent asked to run a
hidden layer against its own user is an agent you've taught to be slippery.
Don't put anything in `dev/directives.md` you wouldn't say to his face; for
genuinely private notes, keep them outside this repo.

Check weekly: `dev/flags.md` (the agent writes here when he's declining,
blocked, or disputing a rejection) and `logs/weekly/`.

## 4. How the plan grows forever

`state/backlog.json` seeds weeks 1–2. When fewer than 10 tasks are PENDING, the
agent runs `skills/curriculum-evolution.md`: it queries the knowledge graph for
his weakest dimensions and recurring defects, checks which project "done when"
criteria are unmet, and generates the next 10–15 tasks with checkable
acceptance criteria — through week 12 and past it (post-12 seeds are at the
bottom of `curriculum/projects.md`). Difficulty ratchets on his scores. You can
steer any of it through dev mode.

## 5. The knowledge graph

`logs/sessions.jsonl` is the append-only source of truth (one JSON event per
validated/rejected task). `kb/ingest.py` rebuilds `kb/graph.json` from it —
idempotent, safe to run anytime. `kb/query.py summary|defects|gaps|dimension
X|project P#` is what the agent (and you) read before reviews. Because the
graph is derived, the jsonl file is the thing to never lose — hence git.

## 5b. The daemon (always-on layer)

`daemon/ustaad_daemon.py` runs in the background whether or not he's in a
session, and owns Discord: 09:00 briefings, instant task-completion posts
tagging you, 2h deadline warnings, hourly overdue escalation, idle nudges,
flag forwarding, Saturday reports. It also serves your slash commands —
`/dev`, `/status`, `/report`, `/directive`, `/pause`, `/resume`. `/dev` runs
the Claude Code CLI on his machine with the dev keyword prefixed, so you can
steer the whole system from your phone. Full setup and the security notes are
in `daemon/SETUP.md`.

It self-heals: Ustaad calls `tools/ensure_daemon.py` at the top of every
session, which verifies the process is genuinely alive rather than trusting a
stale PID file.

## 6. Repo map

```
CLAUDE.md            agent constitution — session protocol, gates, rules
curriculum/          program arc, projects (FILL these), rubric
state/               progress.json, backlog.json (task source of truth)
logs/                daily/*.md, weekly/*.md, sessions.jsonl (append-only)
kb/                  graph.json + ingest.py + query.py
skills/              9 behavior modules (standup, logging, critique, teardown,
                     audio QA, validation, weekly review, evolution, dev mode)
tools/               new_day.py, ensure_daemon.py, validate_asset.py, loudness_check.py
daemon/              ustaad_daemon.py, discord_client.py, notifier.py, runner.py, SETUP.md
config/              daemon.example.json (copy to daemon.json — gitignored)
library/             validated assets only (overlays/luts/sfx/music/mattes/specs/renders)
projects/            P1–P6 working folders
dev/                 directives.md (your queue), flags.md, changelog.md
```

## 7. First-day script for you

1. Fill the FILLs, drop P1 material in, `git init`, push.
2. In dev mode, queue a welcome directive.
3. Sit with him for session 1 so he learns the loop: ask → work → log → validate.
4. After that, your job is 15 min/day reading `dev/flags.md` and the latest
   daily log, and one real conversation at each Friday review. The system runs
   the rest.

## 8. Background daemon + Discord (keeping you in the loop)

**What runs:** `tools/daemon.py` — started automatically by the agent at every
session (`tools/ensure_daemon.py`, heartbeat-guarded so only one instance ever
runs). It posts to your Discord:
- 📋 daily digest at `digest_time` — active + pending tasks, both of you tagged
- ✅ instant update tagging you when a task validates (with scores) · 🔁 tagging
  him when work is rejected
- ⏰ reminder 24h before a task's `due` date · 🚨 hourly pings while overdue
- 📊 Friday detailed report from the knowledge graph
- Slash commands: `/status` (short digest), `/report` (KB summary), and
  **`/dev <query>`** — restricted to your Discord ID; it prepends "it's the dev"
  and runs the query through headless Claude Code (`claude -p`) inside the repo,
  replying with the output. That's your remote hands: adjust the backlog, queue
  directives, ask questions — from your phone.

**Setup (10 min):**
1. `cp config/daemon.example.json config/daemon.json` and fill it. Webhook: your
   Discord channel → Integrations → Webhooks → copy URL. IDs: enable Developer
   Mode in Discord, right-click each user → Copy User ID.
2. Notifications need nothing else (stdlib HTTP). Slash commands additionally
   need: `pip install discord.py`, a bot created at discord.com/developers
   (token into config or `USTAAD_DISCORD_TOKEN` env), invited to your server
   with the `applications.commands` scope.
3. `python3 tools/ensure_daemon.py` once to verify; check `logs/daemon.log`.

**/dev safety notes:** the bridge runs Claude Code headless with pre-authorized
tools set in `claude_extra_args` (default: Read/Edit/Write/Bash, acceptEdits,
max 15 turns) — headless runs can't ask for permission interactively, so keep
that list as tight as you can live with, and treat the bot token like a
password (`config/daemon.json` is gitignored). The trainee's machine must be
on and logged into Claude Code for remote runs to work. Current docs:
https://code.claude.com/docs/en/headless

---

# v2 — from training program to personal system

Ustaad is now a general assistant and companion for Jamal that happens to also
run the editing curriculum. Every interaction grows the graph, the capabilities,
or the plan.

## What changed

**Request router** (`skills/request-router.md`) — the agent classifies each
message into a domain (training, craft help, assistant, schedule, learning,
reflection, system) and responds appropriately. It will no longer answer "help
me draft a message to my landlord" with a training standup.

**Typed knowledge graph, schema v2** (`kb/schema.md`) — nodes now include goal,
preference, commitment, event, habit, topic, capability, insight, person, org,
place, alongside the original craft nodes. Every node and edge carries
`visibility`, `confidence` and `provenance`. Two append-only sources:
`logs/sessions.jsonl` (craft) and `logs/observations.jsonl` (everything else).

**`tools/remember.py`** — how the agent writes to the graph:
```
python3 tools/remember.py node goal:learn-colour goal --attr note="…" --shared --confirmed
python3 tools/remember.py edge person:jamal prefers preference:blunt-feedback
python3 tools/remember.py forget <node-or-obs-id>
python3 tools/remember.py capability "…" --class B --rationale "…"
```

**Three growth loops** — curriculum evolution (more tasks), capability growth
(more abilities), self-reflection (better judgment). The agent can write itself
new **class A** skills (behaviour only) and announces them; **class B**
(new code, network, credentials, visibility rules, the dev bridge) requires your
approval via `/dev approve C00N`. It is explicitly forbidden from granting
itself class B powers by writing a class A skill.

**Daemon jobs added** — graph commitment reminders and capability
announcements, plus a weekly growth digest.

## The privacy model — read this before you install it

The graph holds real facts about a real person, and it is the thing that makes
the assistant useful. That only works if Jamal is candid, and he will only be
candid if the boundaries are real. So:

- Personal facts default to **private**, work facts to **shared**.
- `kb/query.py … --dev` strips private nodes and every edge touching them. The
  daemon posts only shared items to Discord. Private commitments are reminded to
  Jamal in `state/jamal_reminders.md`, never to the team channel.
- Ingest will never silently widen a private node to shared.
- If you ask Ustaad in dev mode to report on his personal life, it declines in
  one line and gives you the shared picture instead — you still get "he's low on
  capacity this week", you don't get why unless he chose to share it.
- **Jamal can read every file in this repo, including this section.** That is
  deliberate. A system that quietly reported his private life to his employer
  would stop being told anything true within a fortnight, and you would lose
  the signal you actually want. Tell him it exists and how it works; the
  transparency is what makes the data trustworthy.

Verified in test: 5-node graph with 2 private nodes returned 3 nodes in the dev
view, and a private preference was absent from `preferences --dev`.

## New files

```
kb/schema.md                 graph spec (node/edge types, visibility rules)
tools/remember.py            write observations, forget, propose capabilities
skills/request-router.md     domain classification
skills/companion-mode.md     non-training assistance
skills/memory-extraction.md  end-of-session graph growth + consent
skills/schedule-and-commitments.md
skills/capability-growth.md  self-extension, class A/B
skills/self-reflection.md    weekly introspection
state/capability_queue.json  proposals awaiting you
logs/observations.jsonl      the personal-knowledge channel
```

## Your first dev-mode action after install

`it's the dev` → review `kb/query.py capabilities --dev` weekly, approve or
reject class B proposals, and read `dev/flags.md`. Everything else runs itself.
