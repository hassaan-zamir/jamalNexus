#!/usr/bin/env python3
"""Rebuild kb/graph.json (schema v2) from logs/sessions.jsonl + logs/observations.jsonl.
Idempotent full rebuild. Observations are the general-purpose channel: any typed
node/edge about Jamal, his work, life, goals, preferences, schedule.

observation record (one JSON per line in logs/observations.jsonl):
{"ts","kind":"node"|"edge"|"forget","obs_id","visibility","confidence","confirmed",
 node: "id","type","attrs"     edge: "src","dst","edge_type","attrs"
 forget: "target"}"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

NODE_TYPES = {"person","project","task","asset","dimension","defect","insight","goal",
              "preference","event","commitment","topic","resource","capability","habit",
              "place","org","day","skill"}

def read_jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: out.append(json.loads(line))
                except json.JSONDecodeError: continue
    except FileNotFoundError: pass
    return out

def main():
    nodes, edges, forgotten = {}, [], set()

    def node(nid, ntype, visibility="shared", **attrs):
        n = nodes.setdefault(nid, {"id": nid, "type": ntype, "visibility": visibility,
                                   "attrs": {}, "provenance": []})
        if ntype: n["type"] = ntype
        if n["visibility"] != "private":   # never silently widen a private node
            n["visibility"] = visibility
        n["attrs"].update({k: v for k, v in attrs.items() if v is not None})
        return nid

    def edge(src, dst, etype, visibility="shared", **attrs):
        edges.append({"src": src, "dst": dst, "type": etype, "visibility": visibility, **attrs})

    obs = read_jsonl(P("logs", "observations.jsonl"))
    for o in obs:
        if o.get("kind") == "forget" and o.get("target"): forgotten.add(o["target"])

    for o in obs:
        if o.get("kind") == "forget": continue
        if o.get("obs_id") in forgotten: continue
        vis, conf = o.get("visibility", "private"), o.get("confidence", 0.8)
        if o.get("kind") == "node":
            nid = o.get("id")
            if not nid or nid in forgotten: continue
            nt = o.get("type", "topic")
            node(nid, nt if nt in NODE_TYPES else "topic", vis, **(o.get("attrs") or {}))
            nodes[nid]["provenance"].append({"obs_id": o.get("obs_id"), "ts": o.get("ts"),
                                             "confidence": conf,
                                             "confirmed": o.get("confirmed", False)})
        elif o.get("kind") == "edge":
            s, d = o.get("src"), o.get("dst")
            if not s or not d or s in forgotten or d in forgotten: continue
            for x in (s, d):
                pre = x.split(":")[0]
                node(x, pre if pre in NODE_TYPES else "topic", vis)
            edge(s, d, o.get("edge_type", "relates_to"), vis, confidence=conf,
                 obs_id=o.get("obs_id"), ts=o.get("ts"), **(o.get("attrs") or {}))

    scores_by_dim = defaultdict(list)
    events = read_jsonl(P("logs", "sessions.jsonl"))
    for e in events:
        day = (e.get("ts") or "")[:10] or "unknown"
        t = node(f"task:{e.get('task_id','?')}", "task", "shared",
                 status=e.get("status"), minutes=e.get("minutes"))
        node(f"day:{day}", "day", "shared")
        edge(t, f"day:{day}", "on_day", "shared")
        if e.get("project"):
            edge(t, node(f"project:{e['project']}", "project", "shared"), "belongs_to", "shared")
        for a in e.get("assets", []) or []:
            edge(t, node(f"asset:{a}", "asset", "shared"), "produced", "shared")
        for dim, v in (e.get("ustaad_scores") or {}).items():
            dn = node(f"dimension:{dim}", "dimension", "shared")
            edge(t, dn, "scored", "shared", value=v, day=day)
            if isinstance(v, (int, float)): scores_by_dim[dim].append((day, v))
        for d in e.get("defects", []) or []:
            edge(t, node(f"defect:{d.lower()}", "defect", "shared"), "exhibited", "shared", day=day)

    for dim, pairs in scores_by_dim.items():
        pairs.sort(); vals = [v for _, v in pairs]; recent = vals[-5:]
        nodes[f"dimension:{dim}"]["attrs"].update({
            "n_scores": len(vals), "avg_all": round(sum(vals)/len(vals), 2),
            "avg_recent5": round(sum(recent)/len(recent), 2),
            "trend": round(sum(recent)/len(recent) - sum(vals)/len(vals), 2)})

    cq = P("state", "capability_queue.json")
    if os.path.exists(cq):
        for c in json.load(open(cq)).get("proposals", []):
            node(f"capability:{c['id']}", "capability", "shared",
                 **{k: c.get(k) for k in ("title", "status", "risk_class", "rationale")})

    graph = {"schema": 2, "nodes": list(nodes.values()), "edges": edges,
             "meta": {"sessions": len(events), "observations": len(obs),
                      "private_nodes": sum(1 for n in nodes.values() if n["visibility"] == "private")}}
    with open(P("kb", "graph.json"), "w") as f:
        json.dump(graph, f, indent=1)
    print(f"kb v2: {len(nodes)} nodes, {len(edges)} edges "
          f"({graph['meta']['private_nodes']} private) from {len(events)} sessions "
          f"+ {len(obs)} observations")

if __name__ == "__main__":
    main()
