# Skill: Asset Validation
Before anything enters library/:
1. `python3 tools/validate_asset.py <path>` — naming, extension, sidecar presence, licence fields.
2. Audio: `python3 tools/loudness_check.py <path> --type sfx|music|narration`.
3. Alpha assets: require his confirmation of an ffmpeg composite test (give him the command: ffmpeg -i bg.mp4 -i overlay.mov -filter_complex overlay -t 5 test.mp4) — Premiere preview is not proof.
4. LUTs: verified via ffmpeg -i in.mp4 -vf lut3d=file.cube.
Reject on any failure with the exact failing check. Log every rejection as a defect in the session event — recurring rejection types feed evolution.
