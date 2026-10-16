# Starting from raw footage and a finished reference

The public example uses generic project names. Substitute the exact projects visible in Borumi. Keep the source recordings and finished reference unchanged; make a separately named working copy for a new full edit. The skill does not promise pixel-identical results or equal model quality.

## Recommended starting model

| Harness | Start the coordinator with | Preparation workers | Escalation |
|---|---|---|---|
| Codex | GPT-6.1 Sol **high effort**, Standard speed, for initial planning and decision/review gates; **medium** for routine execution when supported | GPT-6 Luna **high** for bounded multi-tool scouting; **low** for simple structured extraction, if this host can select it | GPT-6 Astra **medium** initially; raise effort only for the unresolved difficult decision |
| Claude Code | Sonnet 5.5 **high effort** for story/cut planning and reviews; **medium** for routine tool work | Haiku 5.5 **medium** for bounded proposals and caption/source findings | Opus 5.5 **medium** initially; **high** when the difficult decision remains unresolved |
| Grok Build | Grok 4.7 **high effort** if available; **medium** for bounded execution | An actually available smaller model; otherwise Grok 4.7 **medium**, with **low** only for simple checks | **high**, then **xhigh** only for a specific unresolved hard task; no invented `max` setting |

These are starting recommendations, not a measured ranking. Do not begin the entire edit on a small model: cut quality, claim interpretation and visual judgment need a capable coordinator. Do not begin the entire edit on the premium model just to supervise scripts. Start with one representative 30–60-second section, compare it to the reference, and keep the route only if it meets the same quality standard. That sample is part of production and should be reused.

Use the model picker or supported runtime configuration before invocation. A prompt cannot guarantee a child model was selected. Ask the coordinator to report actual assignments and fallbacks in its job folder. Per-harness mechanisms and current official sources are in [model routing](model-routing.md).

High effort at the start helps reconcile narrative, reference style, evidence risks and task dependencies. Delegation itself is routine once those are explicit. Set worker effort separately. A small model may need higher effort for reliable multi-tool work, while a premium model can start at medium. These effort labels do not imply equal compute across providers. If the host cannot switch coordinator effort cleanly within a run, leave it high and bound the workers; no repeated manual switching is required.

## Copy this starter prompt

In Codex, start with `$video-edit-pipeline`. In Claude Code or Grok Build, start with `/video-edit-pipeline` after installation. Follow it with:

```text
Use the raw Borumi project “Tutorial raw” as the source and the current finished
“Tutorial” video as the style and quality reference. Locate both and verify
their identities from the actual files/project state. Make a new working copy
named “Tutorial — pipeline draft”; preserve the raw source and finished reference.

Produce a tightly edited full video in the established style: real screenshots
and tweets as proof, clear demonstrations, readable panels, the existing camera
treatment, chapter/step structure, accurate captions and clean synchronized audio.
Match the reference's pacing and visual language without copying factual mistakes.

Use the staged pipeline. First inspect the reference and reuse existing research,
captures, templates and timed transcripts. Prepare cut candidates and missing-source
leads in parallel, then have the capable coordinator decide the cuts. Apply and
verify the cut before building timed visualizations. Refresh the post-cut timings.
Verify evidence for retained claims, prepare finishing assets, preview visuals,
place them through one timeline writer, and review the actual final export.

Use at most two preparation workers at once. Use small models for candidate cuts,
source discovery and caption findings; use the capable coordinator for decisions,
proof verification and final review. Escalate only difficult unresolved tasks.
Use high coordinator effort for planning and decision/review gates, medium for
routine execution when supported. Use Haiku 5.5 at medium; use GPT-6 Luna at high
for multi-tool scouting or low for simple extraction. In Grok, use medium for
bounded workers and low only for simple checks. Set model and effort explicitly
per worker; verify the actual assignment and report unsupported settings/fallbacks.
Use local code for timing, hashes, subtitle mapping, rendering and technical checks.

Build and review one representative 30–60-second section first, then continue
with that treatment if it matches the reference. Start a separate scene-scoped
pilot job using --scene; do not schedule the full video before the pilot gate.
Save decisions and checkpoints.
Use existing authorized tools and capacity; do not buy subscriptions or switch to
extra API/generation billing without an agreed budget. Flag unsupported claims.
Finish with the reviewed master, corrected captions, chapters, source ledger,
review evidence and a concise report. Do not upload or publish the video.
```

Do not silently reinterpret “raw” as an edited project or recreate missing original camera quality by cropping a flattened master. When the exact source or reference is missing, finish the inventory and report that specific blocker.

## Make the pilot scope real

An unscoped proof job prepares every narration scene before cut assembly. For the pilot, select a representative scene ID from the actual snapshot. The coordinator can inspect the compact scene list without launching scene workers. Initialize a separate job with that ID:

```bash
python3 <skill>/scripts/run.py init '<pilot job>' --mode proof \
  --scene '<actual representative scene ID>' --max-workers 2 \
  --goal 'Match the finished reference in this pilot scene; preserve all other scenes and source media.'
python3 <skill>/scripts/run.py ingest '<pilot job>' \
  --snapshot '<working-copy baseline.json>' --transcript '<timed words directory>'
python3 <skill>/scripts/run.py pipeline '<pilot job>' --format mermaid
python3 <skill>/scripts/run.py next '<pilot job>'
```

The runner scopes scenes, not seconds. Prefer a scene near the desired 30–60 seconds. If it is longer, put the exact review interval and protected surrounding ranges in the goal/brief; do not invent a `--range` option. The cut plan must preserve the untargeted ranges. Add `--plan-only` to the initialization for a proposed treatment without execution.

When the pilot passes its requested review, create a separate full-production job from a **fresh snapshot of the same working copy**. Pass the accepted style specification, proof captures, templates and pilot review by explicit artifact path. Protect the accepted pilot treatment; change it only for a concrete continuity issue. Reuse assets by content, but remap their placements to the final post-cut timing. Do not reuse the pre-pilot timeline snapshot or expand the old pilot job into a different full-video baseline behind its receipts.

## Three useful variants

**Prepare first:** add “Preparation only: show the cut plan, proof gaps, model assignments and proposed visuals. Use `--plan-only`. Do not apply edits, generate paid assets or render the final video.” The deliverable is a handoff, not a finished edit.

**Reels from the accepted master:** add “After the master passes review, propose three self-contained reel candidates and render the strongest one using the existing proof pack and original camera/screen layers where available. Keep captions and evidence readable on a phone.” Use a separate reel job anchored to the reviewed master's path/hash; do not restart the original research.

**Continue in another harness:** use the prompt below with the new provider's invocation prefix:

```text
Resume the existing job at <local job folder>. Read its goal, checkpoint,
current pipeline and unresolved findings. Verify the saved artifacts and current
Borumi revision. Reuse accepted decisions and sources, then run only ready work.
Preserve the working project, raw source and reference. Use this harness's actual
supported models and effort settings for the recorded roles and report any fallback.
Keep one writer.
```

## What should become more efficient

The reference is inspected once to establish a treatment. Workers see only their scene or claim cluster. Removed narration gets no polished asset. Final captions, audio assembly and visual timing wait for the cut. Accepted templates and proof are reused across the long video and reels. Local tools do mechanical work. Checkpoints prevent a harness change from restarting the edit. One focused correction is cheaper than an unlimited small-model retry loop; repeated failure escalates.

Model choice can reduce inference cost, but subscription quota rules are provider-specific. More parallel workers can reduce waiting while consuming more allowance. Measure accepted quality, elapsed time, corrections and the actual usage meter on the same representative section before claiming savings. The same skill provides shared inputs and checks across harnesses; it does not make different models equivalent.
