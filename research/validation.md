# Validation and limits

Checked 2026-10-16. This separate fork preserves the working `video-edit-fast` and `proof-first-video-editor` installations. Private source media, transcripts, screenshots, account details, and receipts were retained outside this repository.

## Foundation checks inherited from video-edit-fast

The checks below were performed on the original portable foundation before the staged pipeline fork. They establish the inherited helper/media baseline, not an end-to-end edit with the new stage graph. New stage-specific checks are recorded separately below.

- Studied the existing public skill and its pinned Borumi, animation, audio, and delivery dependencies. The new entrypoint loads only stage-specific references and does not require Claude's Workflow tool.
- Inventoried 58 local Borumi bundles and inspected metadata in 13. Sampled 20 frames across three long videos and one reel. This establishes observed style and workflow patterns, not a complete quality audit of every video.
- Read a real current project through the existing bridge and the new isolated bridge. Ingested its snapshot plus 17 transcript files: 23 scenes and 4,685 timed words. No original timeline was changed.
- Tested the foundation skill installation. Grok Build 1.0.60 `inspect --json` discovered `video-edit-fast` in the shared skills directory and marked it user-invocable. The same directory is documented for Codex; the installed Codex CLI reported ChatGPT login. A full editing run in every harness has not been performed.
- Passed **37 Python tests and 5 Node tests** covering task dependency ordering, preparation-only stops, immutable receipts, changed-input invalidation, source cache integrity, explicit rate arithmetic, installation preservation, frame-range validation, and subtitle remapping.
- Rendered a six-second, two-range private rough reel from an existing master. FFprobe verified the planned 360×640 dimensions, 30 fps, six-second duration, and audio. A frame was visually inspected. This is an extraction/composition smoke test, not a finished publishable reel.
- Rendered the styled template with synthetic still, camera, and proof-video inputs. Verified a five-second 540×960/30 fps output with AAC audio, correct visible source-time trimming, a 1080×1920 CTA still, and a full 1080×1920/30 fps four-second synthetic video with AAC audio. Neutral fixtures contain no creator media.
- Ran a separate realistic forward test: prepare only an opening-scene edit, identify a possible proof visual, keep unresolved source questions, and hand off between harnesses. This exposed the need for explicit preparation-only state and revisable checkpoints. The package was updated rather than treating a plan as a completed edit.

## Measured context reduction

One project's raw snapshot and timed transcript files occupied **291,495 bytes**. Its compact scene index occupied **16,027 bytes**. Across the 12 substantive narration scenes, median research packet size was **1,961 bytes** (range 861–6,496); median planning packet size was **14,479 bytes** (range 3,591–64,711). Eleven structural scenes were retained for coverage review without separate narration workers.

These are exact file-payload measurements from that snapshot, not measured model-token savings, quota savings, or billing savings. Scene complexity varies. The research packet omits unrelated timeline details; the planning packet retains exact timings needed to prepare edits. Long scenes can still benefit from narrower task slices.

The original entrypoint contained 5,982 whitespace-separated words. The portable entrypoint is under 1,000 words; substantial instructions remain available in references and are loaded when needed. This improves initial context size without removing verification duties.

## New staged-pipeline checks

- Passed **45 Python tests and 5 Node tests** in the fork. Eight added regression cases exercise the v2 graph, role metadata, preparation-only boundaries, immutable stage inputs, committed readback/post-cut hash matching, downstream timing refresh, revised cut ingestion and unchanged v1 compatibility.
- An independent consumer used the real saved 23-scene snapshot and timed words in a private proof-mode `--plan-only` job. It generated 12 cut-candidate tasks, 12 source-discovery tasks and one capable cut-assembly task. JSON and Mermaid matched; zero writers, renders or exports were scheduled, and no editorial milestone was falsely completed.
- That consumer check identified two documentation/contract gaps: a pilot must use explicit scene scope, and a preparation handoff must include requested style/visual/model proposals. The starter scenario now includes a scoped-pilot recipe; the assembly task includes those requested handoff elements. The supplied snapshot alone does not establish the identity of a raw project and a finished reference.
- Installed the fork under its separate shared skill name and Claude skill path, fetched its isolated toolchain on port 47813, and verified Grok Build discovers it as user-invocable. The original portable checkout stayed clean at `18b51d1`; its installed symlink still points there. The original proof-first checkout also remained clean.
- Inspected the interactive map in a desktop browser. Tested stage selection, provider model changes, quick mode skipping new proof/visual production, reel mode using local composition rather than a timeline writer, mobile stage details and no horizontal overflow at 390 CSS pixels. No page JavaScript errors occurred.
- Verified current model/effort recommendations against the official sources in the routing guide. Local CLI help confirmed Grok's `--reasoning-effort`/`--effort` alias and Claude Code 2.1.301's session `--effort`. Actual runtime child model/effort still must be inspected during a real edit.

No new full video was edited as part of these checks. The new writer/stage transitions were exercised with offline test evidence, not new production commits to Borumi. The visual map is an explainer; per-job Mermaid/JSON shows actual recorded tasks, but the harness remains responsible for execution and editorial review.

## Reproduce checks

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_reel_template.mjs
python3 skills/video-edit-pipeline/scripts/run.py doctor
node skills/video-edit-pipeline/scripts/render_reel_template.mjs \
  --plan skills/video-edit-pipeline/assets/reel-template/example.json --check
```

The public example is synthetic and can be rendered using the template's README. The skill-creator frontmatter validator was also run successfully. CI exercises portable helpers without private media or a live Borumi installation.

## What is not established

No controlled cheaper-model-versus-original full-video benchmark was completed. No percentage reduction in Claude quota, no guaranteed wall-clock speedup, and no equal-quality claim across all models is asserted. That experiment needs matched scenes, identical acceptance criteria, and measured repair/review work. See [quota workflow](../skills/video-edit-pipeline/references/quota-workflow.md).

The runner creates a task manifest; the harness dispatches work. Its cost estimator is not a hard spending cap. Its structural verifier cannot certify source truth, visual quality, listening review, or publication. Its model recommendations are starting points, not enforced routing. Public source research and connected service availability do not establish that the same connector is configured in another harness.

Existing Borumi transaction writers are reused at pinned versions. The new bridge declines automatic elicitation. Actual editing must still preserve the raw source, use staged checks and current IDs, and read back committed state. Some agent terminals terminate detached children; keep the bridge in a retained terminal session when necessary. A reconnected bridge needs fresh project/segment discovery even when aliases look familiar.

No videos, source packs, or messages were published as part of this validation. The public deliverable is the reusable skill and its code, research, and synthetic template.
