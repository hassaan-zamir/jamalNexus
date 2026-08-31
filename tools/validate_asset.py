#!/usr/bin/env python3
"""Validate an asset against house standards before it enters library/.
Usage: python3 tools/validate_asset.py <path> [<path> ...]
Checks: naming convention, extension/type match, JSON sidecar, licence fields.
Exit 0 = all pass, 1 = any failure."""
import json, os, re, sys

NAME_RE = re.compile(
    r"^(trans|overlay|matte|lut|sfx|amb|music|spec|render)"
    r"_([a-z0-9]+(?:-[a-z0-9]+)*)"          # category
    r"_([a-z0-9]+(?:-[a-z0-9]+)*)"          # descriptor
    r"(?:_(\d{2,3}|[A-G](?:min|maj)|[a-z0-9-]+))*"  # optional spec fields (bpm/key/etc.)
    r"_v\d{2}"
    r"(?:_[a-z0-9-]+)*"                      # optional trailing spec (e.g. 08f, 30s)
    r"\.(mov|webm|mp4|png|cube|wav|psd|aep|prproj|ai|json|md)$"
)
EXT_FOR_TYPE = {
    "trans": {"mov", "webm", "mp4", "png"}, "overlay": {"mov", "webm", "mp4", "png"},
    "matte": {"mp4"}, "lut": {"cube"}, "sfx": {"wav"}, "amb": {"wav"},
    "music": {"wav"}, "spec": {"psd", "aep", "prproj", "ai", "md", "json"},
    "render": {"mp4", "mov"},
}
LICENCE_KEYS = {"source", "licence", "commercial_ok", "licence_verified_by", "licence_verified_on"}
SIDECAR_EXEMPT = {"spec", "render"}

def check(path):
    errs, warns = [], []
    fname = os.path.basename(path)
    if not os.path.exists(path):
        return [f"file not found: {path}"], warns
    m = NAME_RE.match(fname)
    if not m:
        errs.append(f"naming: '{fname}' does not match "
                    "{type}_{category}_{descriptor}_vNN[_spec].{ext} (lowercase, hyphens inside fields)")
        return errs, warns
    atype, ext = m.group(1), fname.rsplit(".", 1)[1]
    if ext not in EXT_FOR_TYPE[atype]:
        errs.append(f"extension: .{ext} not allowed for type '{atype}' (allowed: {sorted(EXT_FOR_TYPE[atype])})")
    if atype not in SIDECAR_EXEMPT and ext != "json":
        sidecar = os.path.splitext(path)[0] + ".json"
        if not os.path.exists(sidecar):
            errs.append(f"sidecar missing: {os.path.basename(sidecar)} (licence metadata is mandatory)")
        else:
            try:
                with open(sidecar) as f: meta = json.load(f)
                missing = LICENCE_KEYS - set(meta)
                if missing: errs.append(f"sidecar missing licence fields: {sorted(missing)}")
                elif meta.get("commercial_ok") is not True:
                    warns.append("commercial_ok is not true — flag to dev before production use")
                if atype == "music":
                    for k in ("bpm", "structure", "lufs_integrated"):
                        if k not in meta: errs.append(f"music sidecar missing '{k}'")
            except json.JSONDecodeError:
                errs.append("sidecar is not valid JSON")
    return errs, warns

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    failed = False
    for path in sys.argv[1:]:
        errs, warns = check(path)
        status = "FAIL" if errs else "PASS"
        failed |= bool(errs)
        print(f"[{status}] {path}")
        for e in errs:  print(f"   ✗ {e}")
        for w in warns: print(f"   ! {w}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
