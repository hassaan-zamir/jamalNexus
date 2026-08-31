#!/usr/bin/env python3
"""Session bootstrap. Run at the start of EVERY session. Prints a JSON context block."""
import json, os, re, sys, time, datetime as dt
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

def load_json(path, default):
    try:
        with open(path) as f: return json.load(f)
    except Exception: return default

def load_events():
    evs = []
    try:
        with open(P("logs", "sessions.jsonl")) as f:
            for line in f:
                line = line.strip()
                if line:
                    try: evs.append(json.loads(line))
                    except json.JSONDecodeError: pass
    except FileNotFoundError: pass
    return evs


def _graph():
    return load_json(P("kb", "graph.json"), {"nodes": []})

def _due_commitments(days=7):
    """Upcoming commitments/events. Includes private ones — this context block is
    for Jamal's own session. Anything dev-facing must use kb/query.py --dev."""
    out, today = [], dt.date.today()
    for n in _graph().get("nodes", []):
        if n.get("type") not in ("commitment", "event"):
            continue
        a = n.get("attrs") or {}
        raw = a.get("date") or a.get("remind_at")
        if not raw:
            continue
        try:
            dd = dt.date.fromisoformat(raw[:10])
        except ValueError:
            continue
        if 0 <= (dd - today).days <= days:
            out.append({"id": n["id"], "date": raw, "visibility": n.get("visibility"),
                        "note": a.get("note")})
    return sorted(out, key=lambda x: x["date"])

def _open_goals():
    return [n["id"] for n in _graph().get("nodes", [])
            if n.get("type") == "goal" and (n.get("attrs") or {}).get("status", "open") == "open"]

def _pending_caps():
    q = load_json(P("state", "capability_queue.json"), {"proposals": []})
    return [{"id": c["id"], "title": c.get("title"), "class": c.get("risk_class")}
            for c in q.get("proposals", []) if c.get("status") == "proposed"]

def main():
    today = dt.date.today().isoformat()
    prog = load_json(P("state", "progress.json"), {})
    backlog = load_json(P("state", "backlog.json"), {"tasks": []})
    tasks = backlog.get("tasks", [])
    events = load_events()

    # Day number: distinct dates with a session event, +1 if today is new
    days_seen = sorted({e.get("ts", "")[:10] for e in events if e.get("ts")})
    day_number = len(days_seen) + (0 if today in days_seen else 1)

    # Streak: consecutive working days (Sun off) ending yesterday/today
    streak, d = 0, dt.date.today()
    seen = set(days_seen) | {today}
    while True:
        if d.weekday() == 6:  # Sunday doesn't break streak
            d -= dt.timedelta(days=1); continue
        if d.isoformat() in seen:
            streak += 1; d -= dt.timedelta(days=1)
        else:
            break

    by_status = defaultdict(list)
    for t in tasks: by_status[t.get("status", "PENDING")].append(t)
    unlogged = [t["task_id"] for t in by_status["IN_PROGRESS"] + by_status["RESULT_LOGGED"]]

    # Pending dev directives
    directives = []
    try:
        with open(P("dev", "directives.md")) as f:
            block = []
            for line in f:
                if line.startswith("## "): block = [line.rstrip()]
                elif block: block.append(line.rstrip())
                if block and re.search(r"status:\s*pending", line, re.I):
                    directives.append("\n".join(block)); block = []
    except FileNotFoundError: pass

    # Weakest rubric dimension over last 10 scored events
    dims = defaultdict(list)
    for e in events[-10:]:
        for k, v in (e.get("ustaad_scores") or {}).items():
            if isinstance(v, (int, float)): dims[k].append(v)
    weakest = min(dims.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))[0] if dims else None

    # Recurring defects (all time, top 3)
    dcount = defaultdict(int)
    for e in events:
        for d_ in e.get("defects", []) or []: dcount[d_.lower()] += 1
    top_defects = sorted(dcount.items(), key=lambda kv: -kv[1])[:3]

    active = (by_status["IN_PROGRESS"] or by_status["BRIEFED"] or [None])[0]
    nxt = by_status["PENDING"][0] if by_status["PENDING"] else None

    # daemon liveness — the agent has no memory of it, so surface it every session
    daemon_pid, daemon_running = None, False
    try:
        with open(P("daemon", "daemon.pid")) as f:
            daemon_pid = int(f.read().strip())
        try:
            os.kill(daemon_pid, 0)
            hb_path = P("daemon", "heartbeat")
            with open(hb_path) as hf:          # zombies pass os.kill; beats don't lie
                daemon_running = (time.time() - int(hf.read().strip())) < 300
        except (OSError, ProcessLookupError, AttributeError):
            daemon_running = False
    except Exception:
        pass

    ctx = {
        "date": today,
        "daemon_running": daemon_running,
        "daemon_pid": daemon_pid,
        "day_number": day_number,
        "streak": streak,
        "belt": prog.get("belt", "White"),
        "phase": prog.get("phase", "P1 Foundations"),
        "active_task": active,
        "next_pending_task": nxt,
        "unlogged_results_BLOCKING": unlogged,
        "pending_dev_directives": directives,
        "weakest_dimension": weakest,
        "recurring_defects": top_defects,
        "backlog_pending_count": len(by_status["PENDING"]),
        "evolution_needed": len(by_status["PENDING"]) < 10,
        "todays_log_exists": os.path.exists(P("logs", "daily", f"{today}.md")),
        "due_commitments": _due_commitments(),
        "open_goals": _open_goals(),
        "pending_capabilities": _pending_caps(),
    }
    json.dump(ctx, sys.stdout, indent=2, default=str)
    print()

if __name__ == "__main__":
    main()
