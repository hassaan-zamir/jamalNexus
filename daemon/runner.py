#!/usr/bin/env python3
"""Runs dev requests through the Claude Code CLI and queues directives.

Every remote query is prefixed with the dev keyword so Ustaad enters dev mode,
exactly as if the dev had typed it locally. Nothing is hidden from the trainee:
the resulting session is logged in the repo like any other.
"""
import datetime as dt
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
DEV_KEYWORD = "it's the dev"


def run_dev_query(query, cfg, log=print):
    """Invoke the agent CLI non-interactively in the repo. Returns text output."""
    cli = cfg.get("command") or ["claude", "-p"]
    timeout = int(cfg.get("timeout_seconds", 600))
    prompt = f"{DEV_KEYWORD}. {query.strip()}"
    cmd = list(cli) + [prompt]
    log(f"[runner] {' '.join(cli)} <prompt {len(prompt)} chars>")
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError:
        return (f"⚠️ CLI `{cli[0]}` not found on the daemon host's PATH.\n"
                f"Set daemon.claude_cli.command in config/daemon.json to the "
                f"correct executable.")
    except subprocess.TimeoutExpired:
        return f"⚠️ Timed out after {timeout}s. Try a narrower request."
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    _append_remote_log(query, out or err)
    if r.returncode != 0 and not out:
        return f"⚠️ CLI exited {r.returncode}:\n```\n{err[:1500]}\n```"
    return out or err or "(no output)"


def _append_remote_log(query, output):
    """Remote dev sessions are recorded in the repo, visible to everyone."""
    os.makedirs(P("logs"), exist_ok=True)
    entry = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "source": "discord/dev",
        "query": query,
        "output_preview": (output or "")[:600],
    }
    with open(P("logs", "remote_dev.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def queue_directive(text):
    """Write guidance to the queue the agent reads at the trainee's next standup."""
    today = dt.date.today().isoformat()
    block = f"\n## {today} — via Discord\n{text.strip()}\nstatus: pending\n"
    path = P("dev", "directives.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(block)
    return f"Queued. He'll see it at his next standup:\n> {text.strip()[:300]}"
