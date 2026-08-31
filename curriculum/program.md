# Program Arc & House Standards

The 12-week arc (details live in the backlog; evolution extends it forever):

| Weeks | Phase | Project | Theme |
|---|---|---|---|
| 1–2 | Foundations | P1 | Premiere fluency + the entire audio stack |
| 3–4 | Foundations | P2, P3 | Colour, LUTs + music library begins |
| 5–6 | Production | P3, P2 | Alpha overlays, mattes + music DB v1 |
| 7–8 | Production | P4 | Graphics, typography, spec writing |
| 9–10 | Integration | P5 | Teardown, replication, Remotion literacy |
| 11–12 | Integration | P6 | QC role + solo episode |

## Daily shape (6 days/wk, ~8h)
A Study 60m · B Drill 90m · C Production 3.5h (ships into the active project) · D Teardown 45m · E Log 15m.

## House standards (validators enforce these)
- **Naming:** `{type}_{category}_{descriptor}_{vNN}_{spec}.{ext}` — lowercase, hyphens inside fields, underscores between. Types: trans, overlay, matte, lut, sfx, amb, music, spec, render.
- **Audio:** SFX WAV 48k/24-bit, −18 LUFS, peak ≤ −6 dBFS. Music WAV 48k/24-bit, −24 LUFS, TP ≤ −1 dBTP. Narration master −16 LUFS integrated, −1 dBTP.
- **Alpha:** ProRes 4444 .mov (primary) + VP9 .webm + PNG seq (archival). Verify through ffmpeg overlay, never trust the Premiere preview.
- **Mattes:** grayscale H.264 CRF 16.
- **LUTs:** 33-point .cube, verified through ffmpeg lut3d.
- **Sidecars:** every library asset has a `.json` sidecar with licence fields (source, licence, commercial_ok, verified_by, verified_on). No sidecar → not in the library.
- **Motion:** text in 400ms / out 250ms, graphic build 800ms, camera push 2500ms; ease-out default.
- **Transition whitelist:** hard_cut, whip_6f, speed_ramp_12f, match_cut, film_burn (era only, ≤2), glitch (failure beats only, ≤1).

## Reference canon
Murch *In the Blink of an Eye* (W1) · Pearlman *Cutting Rhythms* (W5+) · Wendover (graphics/type) · Johnny Harris (archive & paper) · MagnatesMedia (story/chapters) · Company Man (the floor) · ColdFusion (tone/restraint) · Ben Marriott (motion) · Cullen Kelly / Waqas Qazi (colour) · easings.net (memorise).
