# Projects — real deliverables for real channels

Every task in the backlog belongs to one of these projects. Each project ships
into an actual Iztraab Labs channel/series AND forces a skill cluster.

> **DEV SETUP:** replace every `[FILL]` with the real channel/series before day 1.
> Ustaad: if you encounter an unfilled `[FILL]`, flag it to the dev and pick the
> closest reasonable stand-in so work never stalls.

---

## P1 — Sound Resurrection (Weeks 1–2)
**Ships to:** one already-published episode of `[FILL: channel/series with weakest audio]`
**Deliverable:** a full audio re-master of an existing episode — narration chain,
music bed re-placement, SFX layer, −16 LUFS master — published as the new version
or used as the series' new audio reference.
**Skills forced:** Premiere fluency, timeline discipline, the entire audio stack.
**Also produces:** narration chain preset, room-tone beds, first 20 SFX assets.
**Done when:** dev A/Bs old vs new and signs off; assets validated into `library/`.

## P2 — The Music Engine (Weeks 3 & 6, runs long)
**Ships to:** `[FILL: series with the worst music problem]` — its next 3 episodes
must be scored entirely from this library.
**Deliverable:** Music DB v1 — 40 tracks, tagged, beat-gridded, structure-marked,
loop-pointed, loudness-normalised, licence-verified, with duration variants.
**Skills forced:** music direction, structural listening, metadata discipline.
**Done when:** an episode is cut using only DB tracks selected by tag query, and
its music placement scores ≥7 on the rubric.

## P3 — The Transition & Grade Pack (Weeks 3–5)
**Ships to:** `[FILL: channel]` — its next episode must use only pack assets.
**Deliverable:** Overlay Pack v1 (30 alpha assets ×3 formats), 15 luma mattes,
LUT Pack v1 (8 .cube, ffmpeg-verified).
**Skills forced:** colour, alpha workflows, export discipline, restraint.
**Done when:** every asset passes `validate_asset.py` and composites correctly
through ffmpeg, and the episode ships.

## P4 — The Paper Trail (Weeks 7–8)
**Ships to:** `[FILL: documentary-style series]`, one full episode.
**Deliverable:** newspaper/document/data-card/timeline component specs (layered
sources + reference renders + zero-question specs) PLUS one episode that uses
them, with the full paper-SFX set.
**Skills forced:** typography, motion timing, spec writing, graphic design.
**Done when:** a developer (or the dev) builds one Remotion component from his
spec without asking a single question.

## P5 — The Clone (Weeks 9–10)
**Ships to:** `[FILL: channel]` as a style upgrade.
**Deliverable:** full teardown dataset (200+ logged cuts) of one reference video
from the target style channel, a findings doc, and a 90-second replication built
from library assets — then the findings merged into the series style rules.
**Skills forced:** analysis, rhythm, everything integrated.
**Done when:** dev can't identify the replication as his in a blind clip test,
or the gap analysis names exactly why.

## P6 — Solo Flight (Weeks 11–12)
**Ships to:** `[FILL: channel/series]` — a real published episode.
**Deliverable:** one full 8-minute episode, script provided, built solo using
library assets + sourced footage, plus the 40-point QC checklist derived from
reviewing 5 pipeline outputs.
**Skills forced:** all six dimensions, QC judgment, finishing.
**Done when:** rubric ≥8 average, no dimension below 7, episode published.

---

## After week 12 (evolution seeds)

- P7 — Remotion authorship: he builds his own components from his own specs.
- P8 — Series ownership: full creative ownership of one series' visual language.
- P9 — Pipeline QC lead: human gate on all machine-assembled output, defect →
  automated-fix proposals.
- P10 — Sound mixing depth: stems, mid-side EQ, mastering chains per series.
Evolution generates concrete tasks for these using the same acceptance-criteria
format as P1–P6.
