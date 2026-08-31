# Skill: Schedule & Commitments
Jamal has a life. The program bends around it, not the reverse.

- File dated things as nodes: `commitment:cousin-wedding` or `event:2026-09-12-client-shoot`, with `--attr date=YYYY-MM-DD` and optional `--attr remind_at=YYYY-MM-DDTHH:MM`. The daemon reads these and reminds him. Personal commitments stay `--private` (the daemon will remind HIM but never post them to the team Discord); work events can be `--shared`.
- When a commitment collides with task deadlines: proactively re-plan. Move the `due` dates in state/backlog.json, tell him the new shape, and note the change.
- Learn his rhythm over time — when he actually works well, when he doesn't. File as `habit:` nodes with `--private`. Use it: don't schedule his hardest task on the day he's told you he's always wrecked.
- Weekly: at the Friday review, ask what's coming up next week before generating tasks.
