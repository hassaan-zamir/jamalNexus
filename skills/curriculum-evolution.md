# Skill: Curriculum Evolution (the infinite plan)
Trigger: backlog PENDING < 10, or dev requests it.
Inputs, in order of authority: (1) dev directives, (2) kb/query.py gaps — weakest dimensions + top recurring defects, (3) curriculum/projects.md unmet "done when" criteria, (4) the phase arc / post-week-12 seeds.
Generate 10–15 tasks as backlog JSON entries:
{"task_id":"T###","project":"P#","title","skill_focus":[dims],"brief":"2–4 sentences, concrete","acceptance":["objectively checkable", "..."],"est_hours":n,"status":"PENDING","created_by":"evolution","rationale":"which gap/defect this targets"}
Rules: every task ships something real for a project; every acceptance criterion is checkable without taste; difficulty ratchets — if his last 5 tasks averaged ≥8, raise scope ~20%; if two rejections in a row, insert a smaller bridging task. Never regenerate a task he already completed. Show the dev-visible rationale in the JSON. Append to state/backlog.json and announce the new arc in one paragraph.

Deadlines: give every generated task a "due" date (ISO), spaced from est_hours at ~6 productive h/day, 6 days/wk. The daemon reminds at T-24h and pings hourly when overdue — so due dates must be realistic, not aspirational.

## v2 inputs
Also read `kb/query.py gaps` for: open goals (a stated goal with no tasks attached is a planning failure), pending capabilities, and his commitments this fortnight (don't stack heavy tasks against a known busy week). If he has stated a learning goal outside the editing curriculum, generate tasks for it too — the program serves him, not only the channel.
