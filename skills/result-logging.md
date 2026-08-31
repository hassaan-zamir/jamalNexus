# Skill: Result Logging (hard gate)
No new task is briefed while any task sits in IN_PROGRESS or RESULT_LOGGED-but-unvalidated.
Collect from him, conversationally, then write:
1. Append to `logs/daily/YYYY-MM-DD.md`:
   `## RESULT {task_id}` — what was produced (asset IDs/paths), time spent, hardest part, self-scores on relevant rubric dimensions (1–10 each, with his one-line reason).
2. Run validators on produced assets (validate_asset.py; loudness_check.py for audio). Paste findings.
3. Your scores next to his, with reasons. Disagreements are teaching moments — explain.
4. Append one JSON line to `logs/sessions.jsonl`:
   {"ts","day","task_id","project","assets":[ids],"self_scores":{},"ustaad_scores":{},"defects":[strings],"minutes","status":"VALIDATED|REJECTED","notes"}
5. If VALIDATED: move asset(s) + sidecars into library/, update backlog status, update progress.json, run `python3 kb/ingest.py`.
6. If REJECTED: write the fix list into the task, status back to IN_PROGRESS.

Insights: the session_summary event's "insights" list is how conversation learning reaches the KB — write them as short, reusable observations ("rushes exports when tired", "ducking improved after A/B drill"), not diary lines. kb/query.py surfaces them at weekly reviews and evolution runs.
