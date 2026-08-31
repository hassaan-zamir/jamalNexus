#!/usr/bin/env python3
"""Write to the knowledge graph and manage capability proposals.

  remember node <id> <type> [--attr k=v ...] [--private|--shared] [--confirmed] [--conf 0.9]
  remember edge <src> <edge_type> <dst>      [same flags]
  remember forget <node-id-or-obs-id>
  remember capability <title> --class A|B --rationale "..." [--spec "..."]
  remember approve <cap-id>        (dev only — records approval)

Node ids are namespaced: person:jamal, goal:learn-colour, preference:feedback-style,
commitment:cousin-wedding, event:2026-09-12-shoot, topic:colour-grading, habit:late-nights.

Everything appends to logs/observations.jsonl and then rebuilds the graph.
Default visibility is PRIVATE — pass --shared only for work/craft/schedule facts
the dev is meant to see."""
import argparse, json, os, subprocess, sys, uuid, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
OBS = P("logs", "observations.jsonl")
CAPQ = P("state", "capability_queue.json")

def append(rec):
    rec.setdefault("ts", dt.datetime.now().isoformat(timespec="seconds"))
    rec.setdefault("obs_id", uuid.uuid4().hex[:10])
    with open(OBS, "a") as f: f.write(json.dumps(rec) + "\n")
    return rec

def reingest():
    subprocess.run([sys.executable, P("kb", "ingest.py")], check=False)

def kv(pairs):
    out = {}
    for p in pairs or []:
        if "=" in p:
            k, v = p.split("=", 1)
            try: out[k] = json.loads(v)
            except json.JSONDecodeError: out[k] = v
    return out

def load_caps():
    if os.path.exists(CAPQ):
        return json.load(open(CAPQ))
    return {"proposals": []}

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("cmd", nargs="?", default="help")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--attr", action="append")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--shared", action="store_true")
    ap.add_argument("--confirmed", action="store_true")
    ap.add_argument("--conf", type=float, default=0.8)
    ap.add_argument("--class", dest="risk", choices=["A", "B"], default="B")
    ap.add_argument("--rationale", default="")
    ap.add_argument("--spec", default="")
    a = ap.parse_args()
    vis = "shared" if a.shared else "private"

    if a.cmd == "node" and len(a.rest) >= 2:
        r = append({"kind": "node", "id": a.rest[0], "type": a.rest[1], "attrs": kv(a.attr),
                    "visibility": vis, "confidence": a.conf, "confirmed": a.confirmed})
        print(f"filed node {r['id']} [{vis}] obs={r['obs_id']}"); reingest()

    elif a.cmd == "edge" and len(a.rest) >= 3:
        r = append({"kind": "edge", "src": a.rest[0], "edge_type": a.rest[1], "dst": a.rest[2],
                    "attrs": kv(a.attr), "visibility": vis, "confidence": a.conf,
                    "confirmed": a.confirmed})
        print(f"filed edge {r['src']} -{r['edge_type']}-> {r['dst']} [{vis}]"); reingest()

    elif a.cmd == "forget" and a.rest:
        append({"kind": "forget", "target": a.rest[0]})
        print(f"forgotten: {a.rest[0]} (and anything derived only from it)"); reingest()

    elif a.cmd == "capability" and a.rest:
        q = load_caps()
        cid = f"C{len(q['proposals'])+1:03d}"
        q["proposals"].append({"id": cid, "title": " ".join(a.rest), "risk_class": a.risk,
                               "rationale": a.rationale, "spec": a.spec, "status": "proposed",
                               "created": dt.datetime.now().isoformat(timespec="seconds")})
        json.dump(q, open(CAPQ, "w"), indent=1)
        print(f"capability {cid} proposed (class {a.risk}). "
              f"{'Write it and announce it.' if a.risk=='A' else 'Needs dev approval.'}")
        reingest()

    elif a.cmd == "approve" and a.rest:
        q = load_caps()
        for c in q["proposals"]:
            if c["id"] == a.rest[0]:
                c["status"] = "approved"
                c["approved_at"] = dt.datetime.now().isoformat(timespec="seconds")
                json.dump(q, open(CAPQ, "w"), indent=1)
                print(f"{c['id']} approved: {c['title']}"); reingest(); return
        print("no such capability id")

    else:
        print(__doc__)

if __name__ == "__main__":
    main()
