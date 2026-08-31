#!/usr/bin/env python3
"""Query the knowledge graph (schema v2).
  summary [--dev]        dimensions, defects, totals, goals, capability queue
  gaps                   weakest dims + recurring defects + uncovered domains (evolution input)
  person                 everything known about Jamal (respects --dev filter)
  goals | commitments | preferences | capabilities
  node <id>              one node + its edges
  defects | dimension <name> | project <P#>
--dev  hides private nodes/edges. ALWAYS pass --dev when producing anything the
       dev will see (dev-mode digests, Discord, weekly reports)."""
import json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = [a for a in sys.argv[1:] if a != "--dev"]
DEVVIEW = "--dev" in sys.argv

def load():
    with open(os.path.join(ROOT, "kb", "graph.json")) as f: g = json.load(f)
    if DEVVIEW:
        g["nodes"] = [n for n in g["nodes"] if n.get("visibility") != "private"]
        keep = {n["id"] for n in g["nodes"]}
        g["edges"] = [e for e in g["edges"]
                      if e.get("visibility") != "private" and e["src"] in keep and e["dst"] in keep]
    return g

def by_type(g, t): return [n for n in g["nodes"] if n["type"] == t]

def main():
    cmd = ARGS[0] if ARGS else "summary"
    g = load(); nodes = {n["id"]: n for n in g["nodes"]}; edges = g["edges"]

    if cmd == "summary":
        print(f"== view: {'DEV (private hidden)' if DEVVIEW else 'FULL'} ==")
        dims = sorted(by_type(g, "dimension"), key=lambda n: n["attrs"].get("avg_recent5", 0))
        if dims:
            print("== craft dimensions (recent5 | all | trend) ==")
            for d in dims:
                a = d["attrs"]
                print(f"  {d['id'][10:]:<20} {a.get('avg_recent5','-'):>4} | {a.get('avg_all','-'):>4} | {a.get('trend','-'):+}")
        dc = defaultdict(int)
        for e in edges:
            if e["type"] == "exhibited": dc[e["dst"]] += 1
        if dc:
            print("== top defects ==")
            for k, v in sorted(dc.items(), key=lambda kv: -kv[1])[:5]: print(f"  {v:>3}x  {k[7:]}")
        goals = by_type(g, "goal")
        if goals:
            print("== goals ==")
            for gg in goals: print(f"  [{gg['attrs'].get('status','open')}] {gg['id'][5:]} — {gg['attrs'].get('note','')}")
        caps = [c for c in by_type(g, "capability") if c["attrs"].get("status") == "proposed"]
        if caps:
            print(f"== capability proposals pending: {len(caps)} ==")
            for c in caps[:5]: print(f"  [{c['attrs'].get('risk_class')}] {c['attrs'].get('title')}")
        m = g["meta"]
        print(f"== totals == nodes:{len(g['nodes'])} edges:{len(edges)} "
              f"assets:{len(by_type(g,'asset'))} sessions:{m.get('sessions')} obs:{m.get('observations')}")

    elif cmd == "gaps":
        dims = sorted(by_type(g, "dimension"), key=lambda n: n["attrs"].get("avg_recent5", 10))[:2]
        dc = defaultdict(int)
        for e in edges:
            if e["type"] == "exhibited": dc[e["dst"]] += 1
        caps = [c["attrs"] for c in by_type(g, "capability") if c["attrs"].get("status") == "proposed"]
        stale = [gg["id"][5:] for gg in by_type(g, "goal") if gg["attrs"].get("status") == "open"]
        print(json.dumps({
            "weakest_dimensions": [{"dim": d["id"][10:], "avg_recent5": d["attrs"].get("avg_recent5")} for d in dims],
            "recurring_defects": [{"defect": k[7:], "count": v} for k, v in sorted(dc.items(), key=lambda kv: -kv[1])[:3]],
            "open_goals": stale,
            "pending_capabilities": [c.get("title") for c in caps],
        }, indent=2))

    elif cmd == "person":
        pid = "person:jamal"
        print(json.dumps(nodes.get(pid, {"note": "no person node yet"}), indent=1))
        rel = [e for e in edges if e["src"] == pid or e["dst"] == pid]
        for e in rel:
            other = e["dst"] if e["src"] == pid else e["src"]
            print(f"  {e['type']:<16} {other:<40} vis={e.get('visibility')} conf={e.get('confidence','-')}")

    elif cmd in ("goals", "commitments", "preferences", "capabilities"):
        t = {"goals": "goal", "commitments": "commitment",
             "preferences": "preference", "capabilities": "capability"}[cmd]
        for n in by_type(g, t):
            print(f"[{n.get('visibility')}] {n['id']}  {json.dumps(n['attrs'])}")

    elif cmd == "node" and len(ARGS) > 1:
        nid = ARGS[1]
        print(json.dumps(nodes.get(nid, {}), indent=1))
        for e in edges:
            if e["src"] == nid or e["dst"] == nid: print(" ", json.dumps(e))

    elif cmd == "defects":
        rows = defaultdict(lambda: [0, ""])
        for e in edges:
            if e["type"] == "exhibited":
                rows[e["dst"]][0] += 1; rows[e["dst"]][1] = max(rows[e["dst"]][1], e.get("day", ""))
        for k, (c, last) in sorted(rows.items(), key=lambda kv: -kv[1][0]):
            print(f"{c:>3}x  last {last}  {k[7:]}")

    elif cmd == "dimension" and len(ARGS) > 1:
        want = f"dimension:{ARGS[1]}"
        for day, v in sorted((e.get("day"), e.get("value")) for e in edges
                             if e["type"] == "scored" and e["dst"] == want):
            print(f"{day}  {v}")

    elif cmd == "project" and len(ARGS) > 1:
        want = f"project:{ARGS[1]}"
        for t in [e["src"] for e in edges if e["type"] == "belongs_to" and e["dst"] == want]:
            assets = [e["dst"][6:] for e in edges if e["type"] == "produced" and e["src"] == t]
            print(f"{t[5:]:<8} status={nodes.get(t,{}).get('attrs',{}).get('status')} assets={assets}")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
