# Skill: Audio QA
House chain (narration): denoise → de-ess → HPF 80Hz → +2dB @ 3.5kHz → comp 3:1 → limiter. Targets: narration −16 LUFS int / −1 dBTP; beds −24 LUFS; duck 6–8dB; SFX −18 LUFS peak ≤ −6dBFS; room tone under everything.
When reviewing audio: run tools/loudness_check.py first, discuss numbers before taste. Common defects to name precisely: pumping (over-compression), harshness 2–5kHz, digital silence between beats, music fighting narration in the 1–4kHz band, SFX with no low-end layer, fade-outs instead of endings.
