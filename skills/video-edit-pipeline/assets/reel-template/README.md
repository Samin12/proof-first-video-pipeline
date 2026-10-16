# Vertical reel template

This is working Remotion source for a portrait camera reel with source cards, yellow heading pills, large yellow-and-white captions, a thin progress bar, and a final CTA. It renders review drafts locally. It does not change a Borumi project.

## Run

From the repository root:

```bash
node skills/video-edit-pipeline/scripts/render_reel_template.mjs \
  --plan skills/video-edit-pipeline/assets/reel-template/example.json \
  --output /tmp/reel-preview.mp4 --still /tmp/reel-preview.png --at 1 \
  --deps "$HOME/.borumi-agent/animation-kit" --quality preview
```

The example is four seconds of explicitly synthetic content. It contains no creator media, logos, or imitation posts.

Use `--quality final` for 1080×1920; preview is 540×960. Both preserve the plan's 30 or 60 fps. To check one frame before rendering motion:

```bash
node skills/video-edit-pipeline/scripts/render_reel_template.mjs \
  --plan /path/to/plan.json --still /tmp/reel-frame.png --at 1 --still-only
```

`--check` validates the plan and probes video ranges without loading Remotion. Existing outputs are refused unless `--overwrite` is supplied. Defaults use two render workers; `--concurrency 1` reduces load.

## Dependencies

Node.js 18+, ffprobe, and matching versions of `remotion`, `@remotion/bundler`, and `@remotion/renderer` are required. The tested versions are pinned in [package.json](package.json). The script checks `--deps`, `REMOTION_DEPS`, this template folder, then the existing Borumi animation kit. It only reads the selected installation and builds in a separate temporary directory.

For a new installation:

```bash
npm install --prefix skills/video-edit-pipeline/assets/reel-template
```

Rendering requires an existing headless browser. A cached Remotion browser in the dependency installation is discovered automatically; otherwise provide `--browser /path/to/chrome-headless-shell`. Browser setup and package installation are separate, one-time steps. The renderer does not automatically download or install anything. Use Remotion under its applicable license.

## Plan contract

[schema.json](schema.json) defines the JSON fields. The CLI also validates constraints that JSON Schema cannot: source duration, caption order, unique scene IDs, total duration, and final CTA placement.

Scenes play consecutively. All times are seconds. `duration_s` and caption times are rounded to composition frames. Camera and video-card `source_start_s`/`source_end_s` use **source-media time**, never the old Borumi timeline. The selected source interval must cover the scene. A camera keeps its sound unless `muted:true`; proof videos are always muted.

```json
{
  "version": 1,
  "fps": 30,
  "scenes": [
    {
      "id": "useful-moment",
      "duration_s": 3,
      "heading": "Show the result",
      "camera": {
        "path": "camera.mov",
        "source_start_s": 12,
        "source_end_s": 15,
        "position": [0.5, 0.4]
      },
      "proof": {
        "path": "verified-capture.png",
        "kind": "image",
        "verified": true,
        "label": "Official documentation · captured YYYY-MM-DD",
        "source_url": "https://example.com/your-actual-source"
      },
      "captions": [
        {"start_s": 0, "end_s": 1.5, "text": "HERE IS THE RESULT", "highlight": ["result"]},
        {"start_s": 1.5, "end_s": 3, "text": "CHECK IT YOURSELF", "highlight": ["check"]}
      ]
    }
  ]
}
```

Replace every placeholder before using that example. Paths are local and relative to the plan file, or absolute. `position:[x,y]` sets the camera crop center from 0 to 1. Without a proof card, the camera fills the portrait frame. With a proof card, the camera becomes a blurred background and the card remains readable. No face tracking or automatic truth checking is performed.

`verified:true` records the caller's prior visual/source check; it does not make the renderer a fact checker. Keep the original capture and its evidence-ledger entry. A real post must come from a real capture. The synthetic fixture is clearly labeled and is never evidence for a claim.

Caption phrases have at most seven words and must not overlap. Use the corrected transcript and its source-to-reel mapping. A final scene may instead have `cta:{"eyebrow":"...","text":"...","subtitle":"..."}`. CTA and captions cannot occupy that scene together. This template handles at most 24 scenes and 180 seconds.

## Output checks and reuse

Each output gets a `.receipt.json` with source, plan, template, and output SHA-256 values, renderer versions, dimensions, fps, and scene frame boundaries. **Receipts contain local source paths; keep them private.** Identical source and template hashes let an orchestrator reuse an existing checked render. The helper itself does not silently reuse or publish files.

Review an opening frame, a proof-card frame, every source change, and the CTA. Watch the rendered file for caption accuracy, portrait crop, and audio continuity. A full-resolution render is still a draft until those checks pass. For a fast approximate reframing without these visuals, use the separate `reel.py` helper.
