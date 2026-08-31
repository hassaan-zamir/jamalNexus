#!/usr/bin/env python3
"""Reads repo state and composes the Discord messages. No Discord API here."""
import datetime as dt
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def read_events():
    evs = []
    try:
        with open(P("logs", "sessions.jsonl")) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        evs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return evs


def backlog_tasks():
    return load_json(P("state", "backlog.json"), {"tasks": []}).get("tasks", [])


def deadlines():
    return load_json(P("state", "deadlines.json"), {})


def task_by_id(tid):
    for t in backlog_tasks():
        if t.get("task_id") == tid:
            return t
    return None


def active_tasks():
    """Tasks the trainee is currently on the hook for."""
    return [t for t in backlog_tasks()
            if t.get("status") in ("BRIEFED", "IN_PROGRESS", "RESULT_LOGGED")]


def pending_tasks():
    return [t for t in backlog_tasks() if t.get("status") == "PENDING"]


def state_digest():
    """Dict of everything the notifier and /status need."""
    prog = load_json(P("state", "progress.json"), {})
    events = read_events()
    tasks = backlog_tasks()
    by_status = defaultdict(int)
    for t in tasks:
        by_status[t.get("status", "PENDING")] += 1

    days = sorted({e.get("ts", "")[:10] for e in events if e.get("ts")})
    dims = defaultdict(list)
    for e in events[-10:]:
        for k, v in (e.get("ustaad_scores") or {}).items():
            if isinstance(v, (int, float)):
                dims[k].append(v)
    dim_avg = {k: round(sum(v) / len(v), 1) for k, v in dims.items()}

    defect_counts = defaultdict(int)
    for e in events:
        for d in e.get("defects") or []:
            defect_counts[d.lower()] += 1

    return {
        "belt": prog.get("belt", "White"),
        "phase": prog.get("phase", "?"),
        "trainee": prog.get("trainee_name", "trainee"),
        "day_number": len(days),
        "last_active": days[-1] if days else "never",
        "counts": dict(by_status),
        "active": active_tasks(),
        "pending": pending_tasks(),
        "dim_avg": dim_avg,
        "weakest": min(dim_avg, key=dim_avg.get) if dim_avg else None,
        "top_defects": sorted(defect_counts.items(), key=lambda kv: -kv[1])[:5],
        "events_total": len(events),
        "assets_total": sum(len(e.get("assets") or []) for e in events),
    }


def fmt_task_line(t, dl=None):
    due = (dl or deadlines()).get(t.get("task_id"), {}).get("due_at")
    due_s = ""
    if due:
        try:
            d = dt.datetime.fromisoformat(due)
            delta = d - dt.datetime.now()
            hrs = delta.total_seconds() / 3600
            due_s = (f" · **OVERDUE {abs(hrs):.0f}h**" if hrs < 0
                     else f" · due in {hrs:.0f}h")
        except ValueError:
            pass
    return (f"`{t.get('task_id')}` **{t.get('title')}** "
            f"({t.get('project')}, ~{t.get('est_hours','?')}h){due_s}")


# ---------------------------------------------------------------- messages
def msg_daily_briefing():
    s = state_digest()
    dl = deadlines()
    lines = [f"**Day {s['day_number'] + 1} · {s['belt']} belt · {s['phase']}**", ""]
    if s["active"]:
        lines.append("__On the hook today__")
        lines += [f"• {fmt_task_line(t, dl)}" for t in s["active"]]
    else:
        nxt = s["pending"][:1]
        lines.append("__Next up__")
        lines += ([f"• {fmt_task_line(t, dl)}" for t in nxt]
                  or ["• backlog empty — Ustaad will run evolution"])
    lines += ["", f"Pending in backlog: **{len(s['pending'])}**"
                  f" · assets shipped: **{s['assets_total']}**"]
    if s["weakest"]:
        lines.append(f"Watch today: **{s['weakest']}** (avg {s['dim_avg'][s['weakest']]})")
    lines.append("\nOpen the repo in Claude Code and ask for your standup.")
    return "\n".join(lines)


def msg_task_event(ev):
    tid = ev.get("task_id", "?")
    t = task_by_id(tid) or {}
    status = ev.get("status", "?")
    scores = ev.get("ustaad_scores") or {}
    avg = round(sum(scores.values()) / len(scores), 1) if scores else None
    assets = ev.get("assets") or []
    if status == "VALIDATED":
        head = f"✅ **{tid} validated** — {t.get('title', ev.get('task_id'))}"
    elif status == "REJECTED":
        head = f"🔁 **{tid} sent back** — {t.get('title', tid)}"
    else:
        head = f"📝 **{tid} logged** ({status})"
    body = [head]
    if avg is not None:
        body.append("Scores: " + ", ".join(f"{k} {v}" for k, v in scores.items())
                    + f" · **avg {avg}**")
    if assets:
        body.append(f"Assets: {len(assets)} — " + ", ".join(f"`{a}`" for a in assets[:6])
                    + (" …" if len(assets) > 6 else ""))
    if ev.get("defects"):
        body.append("Defects: " + ", ".join(ev["defects"][:5]))
    if ev.get("minutes"):
        body.append(f"Time: {int(ev['minutes'])} min")
    return "\n".join(body)


def msg_deadline_warning(t, hours_left):
    return (f"⏳ **{t['task_id']}** due in ~{hours_left:.0f}h — {t.get('title')}\n"
            f"If it won't land, log a partial result rather than going silent.")


def msg_overdue(t, hours_over, n):
    urgency = "🔴" if hours_over > 6 else "🟠"
    tail = ("\nThis is the third-plus reminder — dev, worth a look."
            if n >= 3 else "")
    return (f"{urgency} **{t['task_id']} OVERDUE by {hours_over:.0f}h** — {t.get('title')}"
            f"{tail}")


def msg_idle(level):
    s = state_digest()
    if level == "nudge":
        return (f"👀 No session logged yet today. "
                f"{len(s['active'])} task(s) open. Everything OK?")
    return ("🟠 Still no activity logged today. Dev, you may want to check in.")


def msg_weekly_report():
    s = state_digest()
    events = read_events()
    week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    recent = [e for e in events if (e.get("ts") or "")[:10] >= week_ago]
    validated = [e for e in recent if e.get("status") == "VALIDATED"]
    rejected = [e for e in recent if e.get("status") == "REJECTED"]
    assets = sum(len(e.get("assets") or []) for e in recent)
    mins = sum(e.get("minutes") or 0 for e in recent)

    lines = [
        f"📊 **Weekly report — {s['trainee']}**",
        f"Belt **{s['belt']}** · phase {s['phase']} · day {s['day_number']}",
        "",
        f"Validated: **{len(validated)}** · sent back: **{len(rejected)}** "
        f"· assets: **{assets}** · logged time: **{mins/60:.1f}h**",
    ]
    if s["dim_avg"]:
        lines.append("Rubric (last 10): " +
                     " · ".join(f"{k} **{v}**" for k, v in sorted(s["dim_avg"].items())))
    if s["top_defects"]:
        lines.append("Recurring defects: " +
                     ", ".join(f"{d} ×{c}" for d, c in s["top_defects"][:3]))
    lines.append(f"Backlog pending: **{len(s['pending'])}**"
                 + (" — evolution will fire" if len(s["pending"]) < 10 else ""))
    lines.append("\n`/report` for detail · `/dev <query>` to intervene")
    return "\n".join(lines)


def msg_status_short():
    s = state_digest()
    dl = deadlines()
    act = "\n".join(f"• {fmt_task_line(t, dl)}" for t in s["active"]) or "• nothing open"
    return (f"**{s['trainee']}** · day {s['day_number']} · {s['belt']} belt · "
            f"last active {s['last_active']}\n{act}\n"
            f"Pending {len(s['pending'])} · assets {s['assets_total']} · "
            f"weakest {s['weakest'] or '-'}")


def msg_report_full():
    s = state_digest()
    dl = deadlines()
    lines = [f"**Full report — {s['trainee']}**",
             f"Day {s['day_number']} · {s['belt']} belt · {s['phase']} · "
             f"last active {s['last_active']}", ""]
    lines.append("__Open tasks__")
    lines += [f"• {fmt_task_line(t, dl)} — _{t.get('status')}_" for t in s["active"]] or ["• none"]
    lines += ["", "__Next 5 pending__"]
    lines += [f"• {fmt_task_line(t, dl)}" for t in s["pending"][:5]] or ["• none"]
    lines += ["", "__Rubric (last 10 scored)__"]
    lines += [f"• {k}: **{v}**" for k, v in sorted(s["dim_avg"].items())] or ["• no scores yet"]
    lines += ["", "__Recurring defects__"]
    lines += [f"• {d} ×{c}" for d, c in s["top_defects"]] or ["• none logged"]
    lines += ["", f"Totals — events {s['events_total']} · assets {s['assets_total']} "
                  f"· pending {len(s['pending'])}"]
    return "\n".join(lines)


# ---------------------------------------------------------------- v2: graph
def graph():
    return load_json(P("kb", "graph.json"), {"nodes": [], "edges": [], "meta": {}})

def shared_nodes(ntypes=None):
    """Nodes safe to show the dev / post to Discord. Private is never returned."""
    out = []
    for n in graph().get("nodes", []):
        if n.get("visibility") == "private":
            continue
        if ntypes and n.get("type") not in ntypes:
            continue
        out.append(n)
    return out

def due_reminders(within_hours=24):
    """(node, when) for commitments/events coming up. Includes PRIVATE ones —
    callers must route those to Jamal locally, never to Discord."""
    now, out = dt.datetime.now(), []
    for n in graph().get("nodes", []):
        if n.get("type") not in ("commitment", "event"):
            continue
        a = n.get("attrs") or {}
        raw = a.get("remind_at") or a.get("date")
        if not raw:
            continue
        try:
            when = dt.datetime.fromisoformat(raw if "T" in raw else raw + "T09:00:00")
        except ValueError:
            continue
        if 0 < (when - now).total_seconds() <= within_hours * 3600:
            out.append((n, when))
    return sorted(out, key=lambda x: x[1])

def msg_commitment(n, when):
    a = n.get("attrs") or {}
    label = a.get("note") or n["id"].split(":", 1)[1].replace("-", " ")
    return f"🗓️ Reminder: **{label}** — {when:%a %d %b %H:%M}"

def pending_capabilities():
    q = load_json(P("state", "capability_queue.json"), {"proposals": []})
    return [c for c in q.get("proposals", []) if c.get("status") == "proposed"]

def msg_capability(c):
    if c.get("risk_class") == "B":
        return (f"🧩 Ustaad proposed a **class B capability** `{c['id']}`: **{c.get('title')}**\n"
                f"> {(c.get('rationale') or '')[:400]}\n"
                f"Needs your approval — `/dev approve {c['id']}`")
    return f"🧩 Ustaad taught itself a new skill: **{c.get('title')}** _(class A)_"

def msg_growth_digest():
    g = graph(); m = g.get("meta", {})
    goals = [n for n in shared_nodes(("goal",))
             if (n.get("attrs") or {}).get("status", "open") == "open"]
    lines = ["🌱 **System growth**",
             f"Graph: **{len(g.get('nodes', []))}** nodes · **{len(g.get('edges', []))}** edges "
             f"· {m.get('observations', 0)} observations",
             f"Open goals: {len(goals)}" + (" — " + ", ".join(n["id"][5:] for n in goals[:4]) if goals else "")]
    caps = pending_capabilities()
    if caps:
        lines.append(f"Capability proposals awaiting you: **{len(caps)}**")
    lines.append("_(private entries are excluded from all reports)_")
    return "\n".join(lines)
