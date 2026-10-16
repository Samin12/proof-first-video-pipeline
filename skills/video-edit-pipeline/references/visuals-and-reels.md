# Visuals and reels

## Reuse the observed style

The sampled long videos use a near-black drifting dot grid, a large left proof panel, a smaller camera tile on the right, and a step badge above the camera. The original MIT toolkit includes the `templates/velour-style` Remotion components and validated Borumi geometry. Reuse that source rather than asking a model to reconstruct it from scratch on every job. Preserve the existing project's chosen variant.

Use a compact list of visual beats: time range, narration purpose, verified asset, template, crop/highlight, and foreground/background role. A source card needs its canonical source and capture date. Use a real screenshot for product state; use a clear diagram for an abstract explanation. A full-screen source may be more legible than squeezing text into a panel.

The original animation kit's `job.mjs` has its own create/typecheck/render/wait commands. Inspect its `--help` and the pinned `references/visual-system.md` before generating a job. Do not execute the original Claude `Workflow(...)` wrapper in a harness that lacks that API; run the roles and scripts directly.

Before rendering, hash the template source/version, input assets, text/data, font set, frame rate, dimensions, and timing. If the same hash already produced an accepted result, reuse it. Check a representative still and a short low-resolution motion preview, including first/last frames, alpha compositing, and source order. Only then render the final clip. Limit parallel renders to spare CPU/GPU capacity; simultaneous model workers do not make one encoder faster.

## Reel workflow

Pick a self-contained hook, demonstration, and payoff from the reviewed master. Return a few strong candidates with source ranges and a reason each works. Use the existing transcript/source pack to avoid researching the same claim again. Keep context needed to understand the result; do not select a misleading fragment solely because it is short.

Create a source-to-output range map **before** laying out captions. The observed reel composition is full-height camera or large proof cards on a blurred background, short yellow/white captions, a thin progress bar, and a closing CTA. A centered crop of a side-by-side master cannot recover a high-resolution camera shot and may remove the evidence. Prefer the original separate camera/screen sources and crop intentionally per shot. Keep proof text readable on a phone. The reusable local template is in `assets/reel-template`; its README documents the renderer, schema, and fixture.

Reframe from sources and use the template for a polished draft. The smaller `scripts/reel.py` helper provides a deterministic **rough draft/fallback**, with contain-and-pad by default or explicit per-shot source-pixel crops:

```json
{
  "source": "/absolute/path/reviewed-master.mp4",
  "fps": 30,
  "size": [1080, 1920],
  "clips": [{"in": 12.0, "out": 23.0}, {"in": 42.0, "out": 51.0}],
  "srt": "/absolute/path/reviewed-master.srt"
}
```

```bash
python3 <skill>/scripts/reel.py '<job>/reel-plan.json' --output '<job>/reel-review.mp4' --plan-only
python3 <skill>/scripts/reel.py '<job>/reel-plan.json' --output '<job>/reel-review.mp4'
```

The helper quantizes ranges to the output frame grid, re-encodes only selected ranges, remaps the optional SRT, and records source/output hashes and exact frame mapping. It refuses overwrites. It does not burn captions, infer speaker crops, create a CTA, guarantee source-level word timing, or certify visual quality. Partially cut subtitle cues are flagged and require review; rewrite them from word timings rather than leaving words no longer spoken.

Render and inspect at phone size. Review every shot change, caption, proof card, and the final CTA. Reels remain drafts until checked; posting, music licensing, a lead magnet, and a comment-to-DM automation are separate tasks, not implied by a video render.

## Audio without unnecessary paid work

Keep acceptable source audio. When needed, use local measurements and a two-pass loudness process at the creator's established target; listen for clipping, pumping, edits and drift. Avoid automatically mastering every source and then mastering the whole mix again. The upstream audio scripts support precise synchronization/joins; read only the relevant operation. Use Auphonic for audio that benefits from it and only within authorized credits. Keep the original audio and verify equal duration/alignment after processing.

Lock narration/cuts before final audio, captions, chapters, and reel maps. A late cut must invalidate those dependent outputs. Never reuse captions from a different edit just because the filename looks similar.
