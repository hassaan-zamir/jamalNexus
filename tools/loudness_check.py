#!/usr/bin/env python3
"""Measure loudness with ffmpeg and compare to house targets.
Usage: python3 tools/loudness_check.py <audio-or-video> --type sfx|amb|music|narration
Targets: sfx/amb −18 LUFS (peak ≤ −6 dBFS) · music −24 LUFS (TP ≤ −1) · narration −16 LUFS (TP ≤ −1)."""
import argparse, json, re, shutil, subprocess, sys

TARGETS = {  # (target_lufs, tolerance, max_true_peak)
    "sfx": (-18.0, 1.5, -6.0), "amb": (-18.0, 1.5, -6.0),
    "music": (-24.0, 1.0, -1.0), "narration": (-16.0, 1.0, -1.0),
}

def measure(path):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH — install it first (see README).")
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
           "-af", "loudnorm=I=-16:TP=-1:LRA=11:print_format=json", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        sys.exit("could not parse loudnorm output — is this an audio-bearing file?")
    d = json.loads(m.group(0))
    return float(d["input_i"]), float(d["input_tp"]), float(d["input_lra"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--type", required=True, choices=TARGETS)
    a = ap.parse_args()
    lufs, tp, lra = measure(a.path)
    tgt, tol, max_tp = TARGETS[a.type]
    ok_l, ok_tp = abs(lufs - tgt) <= tol, tp <= max_tp
    print(f"file: {a.path}\ntype: {a.type}")
    print(f"integrated: {lufs:+.1f} LUFS  (target {tgt:+.1f} ±{tol})   {'OK' if ok_l else 'FAIL'}")
    print(f"true peak : {tp:+.1f} dBTP  (max {max_tp:+.1f})          {'OK' if ok_tp else 'FAIL'}")
    print(f"LRA       : {lra:.1f} LU")
    if not ok_l:
        print(f"fix: apply gain of {tgt - lufs:+.1f} dB, or re-master.")
    sys.exit(0 if (ok_l and ok_tp) else 1)

if __name__ == "__main__":
    main()
