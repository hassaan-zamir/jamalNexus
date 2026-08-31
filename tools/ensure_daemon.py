#!/usr/bin/env python3
"""Ensure the background daemon is running. Ustaad calls this FIRST every session.

Cross-platform, no dependencies. Detects a stale PID file, verifies the process
is actually alive, and relaunches detached if not.

    python3 tools/ensure_daemon.py           # start if down, report either way
    python3 tools/ensure_daemon.py --status  # report only, never start
    python3 tools/ensure_daemon.py --restart # kill and relaunch
"""
import argparse, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
PIDFILE = P("daemon", "daemon.pid")
ENTRY = P("daemon", "ustaad_daemon.py")

HEARTBEAT = P("daemon", "heartbeat")
STALE_AFTER = 300  # seconds; poll is 60s, so 5 missed beats means dead


def heartbeat_fresh():
    try:
        with open(HEARTBEAT) as f:
            return (time.time() - int(f.read().strip())) < STALE_AFTER
    except Exception:
        return False



def read_pid():
    try:
        with open(PIDFILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def alive(pid):
    """A PID alone is not proof — zombies answer signal 0. Require a fresh beat."""
    if not pid:
        return False
    if not heartbeat_fresh():
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill(pid):
    if not pid:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            os.kill(pid, 15)
    except OSError:
        pass


def start():
    os.makedirs(P("logs"), exist_ok=True)
    logf = open(P("logs", "daemon.out"), "a")
    kwargs = {"cwd": ROOT, "stdout": logf, "stderr": logf, "stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED | NEW_GROUP
    else:
        kwargs["start_new_session"] = True
    p = subprocess.Popen([sys.executable, ENTRY], **kwargs)
    for _ in range(20):
        time.sleep(0.25)
        if alive(read_pid()):
            return read_pid()
    return p.pid if alive(p.pid) else None


def config_ready():
    try:
        with open(P("config", "daemon.json")) as f:
            cfg = json.load(f)
        return bool((cfg.get("discord") or {}).get("webhook_url"))
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--restart", action="store_true")
    a = ap.parse_args()

    pid = read_pid()
    running = alive(pid)
    result = {"was_running": running, "pid": pid,
              "config_ready": config_ready(), "action": "none"}

    if a.status:
        pass
    elif a.restart:
        kill(pid); time.sleep(1)
        result["pid"] = start(); result["action"] = "restarted"
    elif not running:
        if not os.path.exists(ENTRY):
            result["action"] = "error: daemon entrypoint missing"
        else:
            result["pid"] = start(); result["action"] = "started"
    else:
        result["action"] = "already running"

    result["running"] = alive(result.get("pid"))
    if not result["config_ready"]:
        result["warning"] = ("config/daemon.json has no webhook_url — daemon runs "
                             "but Discord notifications are disabled. Tell the dev.")
    json.dump(result, sys.stdout, indent=2); print()


if __name__ == "__main__":
    main()
