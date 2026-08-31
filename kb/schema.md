# Knowledge Graph — schema v2

Two append-only sources, one derived graph. `kb/graph.json` is rebuilt from scratch by `kb/ingest.py`; never edit it by hand.

- `logs/sessions.jsonl` — craft training events (always `shared`)
- `logs/observations.jsonl` — everything else: typed nodes/edges about Jamal, written via `tools/remember.py`

## Node types
person, project, task, asset, dimension, defect, insight, goal, preference, event, commitment, topic, resource, capability, habit, place, org, day, skill

Ids are namespaced `type:slug` — `goal:learn-colour`, `preference:blunt-feedback`, `commitment:cousin-wedding`, `habit:late-nights`, `topic:colour-grading`.

## Edge types
belongs_to, produced, on_day, scored, exhibited, prefers, works_on, blocked_by, learned_from, scheduled_at, depends_on, relates_to, motivated_by, struggles_with, improved_at, knows, attends

## Every node and edge carries
`visibility` (shared | private | system) · `confidence` (0–1) · `provenance` (obs_id, ts, confirmed)

## Visibility rules (enforced in code and in CLAUDE.md)
- ingest never widens an existing `private` node to `shared`
- `kb/query.py ... --dev` strips private nodes and any edge touching them
- the daemon posts only `shared` items to Discord
- private material exists to serve Jamal; it is not reporting data

## Growth
Sessions grow the craft subgraph. Observations grow the person subgraph. The capability queue grows the system itself. All three feed `kb/query.py gaps`, which drives curriculum evolution, capability growth and weekly reflection.
