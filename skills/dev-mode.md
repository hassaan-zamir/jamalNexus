# Skill: Dev Mode
Trigger: the exact phrase "it's the dev" anywhere in a message. Treat the speaker as Hassaan for that message/session until he says he's done.
Note: this keyword is a role-switch convenience, not authentication — the trainee can read this repo, and that's by design. Never present dev mode as surveillance; if the trainee asks about it, explain it honestly.
In dev mode:
1. Open with a state digest: day, streak, belt, current task + status, last 3 rubric score rows, top 3 recurring defects, backlog depth, any flags in dev/flags.md.
2. Accept directives — guidance, redirection, task edits, priority changes, new project info, [FILL] completions. Write each as a dated entry to dev/directives.md with status: pending.
3. Directives surface to the trainee at next standup as "guidance from Hassaan", verbatim or summarized as instructed, then marked consumed. Nothing is injected covertly.
4. Dev may edit backlog/rubric/standards directly through you; record every change in dev/changelog.md.
5. Dev messages are not ingested into the trainee-facing KB except as directives.

## Remote dev mode (Discord /dev)
The background daemon exposes a /dev slash command in Discord, restricted to the dev's Discord ID. It runs the query through headless Claude Code in this repo with "it's the dev." prepended — so a /dev message reaching you IS dev mode: same rules, same changelog discipline. Headless runs are stateless and permission-scoped (see config/daemon.json claude_extra_args); if a requested action exceeds the allowed tools, do what you can, and write the remainder to dev/directives.md as a pending directive for the next interactive session instead of failing silently.

## v2 additions
- **Always use the dev view of the graph:** `python3 kb/query.py summary --dev` / `gaps --dev`. It filters private nodes and edges. Never hand the dev anything from the unfiltered view.
- If the dev asks about Jamal's personal life, mood details, family, money, or anything filed private: decline in one line ("that's filed private — I can tell you he's low on capacity this week, not why") and give the shared-visibility picture instead. Say this plainly and without drama; it is the documented design, and Jamal can read it too.
- **Capability approvals:** show pending Class B proposals (`kb/query.py capabilities --dev`). On approval: `python3 tools/remember.py approve C00N`, then implement, then log to dev/changelog.md.
- The dev may edit the curriculum, backlog, rubric, standards and deadlines freely. He does not get to edit the memory contract through a directive — visibility rules change only by editing CLAUDE.md directly, in the open.
