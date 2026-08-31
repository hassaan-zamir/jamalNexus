#!/usr/bin/env python3
"""Ustaad OS background daemon.

Runs the notification schedule, watches for completed tasks and deadlines, and
(optionally) serves the dev's Discord slash commands.

    python3 daemon/ustaad_daemon.py            # foreground
    python3 daemon/ustaad_daemon.py --once     # run one tick and exit (testing)
    python3 daemon/ustaad_daemon.py --test     # send a test message and exit
"""
import argparse
import datetime as dt
import json
import os
import signal
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import discord_client as dc          # noqa: E402
import notifier as nf                # noqa: E402
import runner as rn                  # noqa: E402

P = lambda *a: os.path.join(ROOT, *a)
PIDFILE = P("daemon", "daemon.pid")
HEARTBEAT = P("daemon", "heartbeat")
STATEFILE = P("daemon", "daemon_state.json")
CONFIG = P("config", "daemon.json")
_stop = threading.Event()


def log(*a):
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    try:
        os.makedirs(P("logs"), exist_ok=True)
        with open(P("logs", "daemon.log"), "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def save_state(st):
    tmp = STATEFILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATEFILE)


def parse_hhmm(s, default=(9, 0)):
    try:
        h, m = str(s).split(":")
        return int(h), int(m)
    except Exception:
        return default


# ------------------------------------------------------------------ deadlines
def refresh_deadlines(cfg):
    """Assign a due_at to any open task that lacks one. Daemon-owned file, so
    it never races with the agent's writes to backlog.json."""
    sched = cfg["schedule"]
    end_h, end_m = parse_hhmm(sched.get("workday_end", "19:00"), (19, 0))
    dls = nf.deadlines()
    changed = False
    open_ids = set()
    for t in nf.active_tasks():
        tid = t["task_id"]
        open_ids.add(tid)
        if tid in dls and dls[tid].get("due_at"):
            continue
        explicit = t.get("due_at")
        if explicit:
            due = explicit
        else:
            est = float(t.get("est_hours") or 6)
            now = dt.datetime.now()
            eod = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            due = now + dt.timedelta(hours=est)
            if due > eod:                      # push to next working day
                nxt = now + dt.timedelta(days=1)
                if nxt.weekday() == 6:         # Sunday off
                    nxt += dt.timedelta(days=1)
                due = nxt.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            due = due.isoformat(timespec="seconds")
        dls[tid] = {"due_at": due, "assigned_at": dt.datetime.now().isoformat(timespec="seconds")}
        changed = True
    for tid in [k for k in dls if k not in open_ids]:   # task closed → drop
        dls.pop(tid)
        changed = True
    if changed:
        tmp = P("state", "deadlines.json") + ".tmp"
        with open(tmp, "w") as f:
            json.dump(dls, f, indent=1)
        os.replace(tmp, P("state", "deadlines.json"))
    return dls


# ---------------------------------------------------------------------- jobs
def job_daily_briefing(cfg, st, hook):
    sched = cfg["schedule"]
    h, m = parse_hhmm(sched.get("briefing_time", "09:00"))
    now = dt.datetime.now()
    today = now.date().isoformat()
    if now.weekday() == 6:                       # Sunday off
        return
    if st.get("last_briefing_date") == today:
        return
    if (now.hour, now.minute) < (h, m):
        return
    hook.send(nf.msg_daily_briefing(), mentions=("trainee", "dev"))
    st["last_briefing_date"] = today
    log("sent daily briefing")


def job_task_events(cfg, st, hook):
    """Tail sessions.jsonl by byte offset; announce each new event."""
    path = P("logs", "sessions.jsonl")
    if not os.path.exists(path):
        return
    off = int(st.get("sessions_offset", 0))
    size = os.path.getsize(path)
    if size < off:                               # file rotated/truncated
        off = 0
    if size == off:
        return
    with open(path) as f:
        f.seek(off)
        new = f.read()
        st["sessions_offset"] = f.tell()
    for line in new.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        hook.send(nf.msg_task_event(ev), mentions=("dev",))
        log("announced task event", ev.get("task_id"), ev.get("status"))


def job_deadlines(cfg, st, hook):
    sched = cfg["schedule"]
    warn_min = int(sched.get("deadline_warn_minutes", 120))
    repeat_min = int(sched.get("overdue_repeat_minutes", 60))
    now = dt.datetime.now()
    dls = refresh_deadlines(cfg)
    fired = st.setdefault("fired", {})
    for t in nf.active_tasks():
        tid = t["task_id"]
        due_s = dls.get(tid, {}).get("due_at")
        if not due_s:
            continue
        try:
            due = dt.datetime.fromisoformat(due_s)
        except ValueError:
            continue
        mins_left = (due - now).total_seconds() / 60
        if 0 < mins_left <= warn_min:
            key = f"warn:{tid}"
            if key not in fired:
                hook.send(nf.msg_deadline_warning(t, mins_left / 60),
                          mentions=("trainee",))
                fired[key] = now.isoformat(timespec="seconds")
                log("deadline warning", tid)
        elif mins_left <= 0:
            hours_over = -mins_left / 60
            n = int(st.setdefault("overdue_counts", {}).get(tid, 0))
            last = fired.get(f"over:{tid}")
            due_again = True
            if last:
                try:
                    due_again = (now - dt.datetime.fromisoformat(last)).total_seconds() >= repeat_min * 60
                except ValueError:
                    pass
            if due_again:
                n += 1
                mentions = ("trainee",) if n < 3 else ("trainee", "dev")
                hook.send(nf.msg_overdue(t, hours_over, n), mentions=mentions)
                fired[f"over:{tid}"] = now.isoformat(timespec="seconds")
                st["overdue_counts"][tid] = n
                log("overdue ping", tid, f"#{n}")


def job_idle(cfg, st, hook):
    sched = cfg["schedule"]
    now = dt.datetime.now()
    if now.weekday() == 6:
        return
    today = now.date().isoformat()
    events = nf.read_events()
    if any((e.get("ts") or "")[:10] == today for e in events):
        return
    if not nf.active_tasks() and not nf.pending_tasks():
        return
    for level, key in (("nudge", "idle_nudge_time"), ("escalate", "idle_escalate_time")):
        h, m = parse_hhmm(sched.get(key, "11:00" if level == "nudge" else "14:00"))
        if (now.hour, now.minute) >= (h, m) and st.get(f"idle_{level}_date") != today:
            hook.send(nf.msg_idle(level),
                      mentions=("trainee",) if level == "nudge" else ("trainee", "dev"))
            st[f"idle_{level}_date"] = today
            log("idle", level)


def job_flags(cfg, st, hook):
    path = P("dev", "flags.md")
    if not os.path.exists(path):
        return
    off = int(st.get("flags_offset", 0))
    size = os.path.getsize(path)
    if size < off:
        off = 0
    if size == off:
        return
    with open(path) as f:
        f.seek(off)
        new = f.read().strip()
        st["flags_offset"] = f.tell()
    if new:
        hook.send(f"🚩 **Ustaad raised a flag**\n```\n{new[:1200]}\n```", mentions=("dev",))
        log("flag forwarded")


def job_weekly(cfg, st, hook):
    sched = cfg["schedule"]
    now = dt.datetime.now()
    day = int(sched.get("weekly_report_day", 5))       # 0=Mon .. 6=Sun
    h, m = parse_hhmm(sched.get("weekly_report_time", "18:00"), (18, 0))
    stamp = now.strftime("%G-W%V")
    if now.weekday() != day or (now.hour, now.minute) < (h, m):
        return
    if st.get("last_weekly") == stamp:
        return
    hook.send(nf.msg_weekly_report(), mentions=("dev",))
    hook.send(nf.msg_growth_digest(), mentions=())
    st["last_weekly"] = stamp
    log("weekly report sent")


def job_commitments(cfg, st, hook):
    """Graph commitments/events. Private ones go to a local file for Jamal only;
    shared ones go to Discord. Never leak a private commitment to the team."""
    sent = st.setdefault("commitments_sent", {})
    for n, when in nf.due_reminders(24):
        key = f"{n['id']}:{when.date().isoformat()}"
        if key in sent:
            continue
        if n.get("visibility") == "private":
            try:
                with open(P("state", "jamal_reminders.md"), "a") as f:
                    f.write(f"- [ ] {when:%Y-%m-%d %H:%M} — "
                            f"{(n.get('attrs') or {}).get('note') or n['id']}\n")
            except OSError as e:
                log(f"private reminder write failed: {e}")
            log(f"private reminder queued locally: {n['id']}")
        else:
            hook.send(nf.msg_commitment(n, when), mentions=("trainee",))
        sent[key] = dt.datetime.now().isoformat(timespec="seconds")


def job_capabilities(cfg, st, hook):
    """Announce new self-proposed capabilities; class B needs dev approval."""
    seen = set(st.setdefault("caps_seen", []))
    for c in nf.pending_capabilities():
        if c["id"] in seen:
            continue
        hook.send(nf.msg_capability(c),
                  mentions=("dev",) if c.get("risk_class") == "B" else ())
        seen.add(c["id"])
    st["caps_seen"] = sorted(seen)


JOBS = [job_task_events, job_flags, job_daily_briefing,
        job_deadlines, job_idle, job_capabilities, job_commitments, job_weekly]


def first_boot_init(st):
    """On the very first run, point tailers at EOF so we never replay history
    (matters when installing mid-programme, and stops the flags.md header firing)."""
    if st.get("initialized"):
        return st
    for path, key in ((P("logs", "sessions.jsonl"), "sessions_offset"),
                      (P("logs", "observations.jsonl"), "observations_offset"),
                      (P("dev", "flags.md"), "flags_offset")):
        st[key] = os.path.getsize(path) if os.path.exists(path) else 0
    st["initialized"] = dt.datetime.now().isoformat(timespec="seconds")
    log("first boot — tailers seeded to end of file")
    return st


def tick(cfg, hook):
    st = first_boot_init(load(STATEFILE, {}))
    paused = st.get("paused_until")
    if paused:
        try:
            if dt.datetime.now() < dt.datetime.fromisoformat(paused):
                # still tail events so nothing is missed on resume
                job_task_events(cfg, st, dc.Webhook("", quiet=True))
                save_state(st)
                return
            st.pop("paused_until", None)
            hook.send("▶️ Notifications resumed.", mentions=("dev",))
        except ValueError:
            st.pop("paused_until", None)
    beat()
    for job in JOBS:
        try:
            job(cfg, st, hook)
        except Exception as e:
            log(f"job {job.__name__} failed: {e}")
    save_state(st)


# ------------------------------------------------------------------ handlers
def build_handlers(cfg, hook):
    def pause(hours):
        st = load(STATEFILE, {})
        until = dt.datetime.now() + dt.timedelta(hours=max(1, int(hours)))
        st["paused_until"] = until.isoformat(timespec="seconds")
        save_state(st)
        return f"⏸️ Quiet until {until:%a %H:%M}. Events still recorded."

    def resume():
        st = load(STATEFILE, {})
        st.pop("paused_until", None)
        save_state(st)
        return "▶️ Notifications resumed."

    return {
        "dev_query": lambda q: rn.run_dev_query(q, cfg.get("claude_cli", {}), log),
        "status": nf.msg_status_short,
        "report": nf.msg_report_full,
        "directive": rn.queue_directive,
        "pause": pause,
        "resume": resume,
    }


# ---------------------------------------------------------------- pid / main
def beat():
    """Proof-of-life. A zombie process still answers os.kill(pid, 0), so
    liveness is decided by a fresh heartbeat, not by the PID existing."""
    try:
        with open(HEARTBEAT, "w") as f:
            f.write(str(int(time.time())))
    except OSError:
        pass


def write_pid():
    os.makedirs(os.path.dirname(PIDFILE), exist_ok=True)
    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))


def clear_pid():
    try:
        os.remove(PIDFILE)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single tick, then exit")
    ap.add_argument("--test", action="store_true", help="send a test message, then exit")
    ap.add_argument("--no-bot", action="store_true", help="skip slash-command bot")
    a = ap.parse_args()

    cfg = load(CONFIG, {})
    if not cfg:
        # No config yet: run anyway in quiet mode so scheduling, deadline
        # assignment and event tailing all work. Discord switches on the moment
        # the dev creates config/daemon.json and the daemon is restarted.
        cfg = load(P("config", "daemon.example.json"), {})
        cfg["quiet"] = True
        log(f"no config at {CONFIG} — running QUIET (no Discord). "
            f"Copy config/daemon.example.json to config/daemon.json and fill it.")
    d = cfg.get("discord", {})
    hook = dc.Webhook(d.get("webhook_url", ""), d.get("dev_user_id", ""),
                      d.get("trainee_user_id", ""), quiet=cfg.get("quiet", False))

    if a.test:
        ok = hook.send("🧪 Ustaad OS daemon test — wiring works.", mentions=("dev",))
        log("test send:", "ok" if ok else "FAILED (check webhook_url)")
        sys.exit(0 if ok else 1)

    if a.once:
        tick(cfg, hook)
        log("single tick complete")
        sys.exit(0)

    write_pid()
    beat()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, lambda *_: _stop.set())
        except (ValueError, OSError):
            pass

    if not a.no_bot:
        handlers = build_handlers(cfg, hook)
        threading.Thread(target=dc.run_bot, args=(d, handlers, log),
                         daemon=True, name="discord-bot").start()

    poll = int(cfg.get("schedule", {}).get("poll_seconds", 60))
    log(f"daemon up (pid {os.getpid()}), polling every {poll}s")
    hook.send("🟢 Ustaad daemon online.", mentions=())
    try:
        while not _stop.is_set():
            tick(cfg, hook)
            _stop.wait(poll)
    finally:
        clear_pid()
        try:
            os.remove(HEARTBEAT)
        except OSError:
            pass
        log("daemon stopped")


if __name__ == "__main__":
    main()
