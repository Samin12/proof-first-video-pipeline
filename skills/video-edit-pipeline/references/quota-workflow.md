# Keep the quality; reduce the repeated work

The production metric is **accepted editing work per unit of subscription usage and elapsed time**, including corrections. A cheap draft that needs a full rewrite is not a saving. Do not replace the creator's successful visual/editorial standard with a cheaper-looking result.

Use [the stage map](pipeline.md) to choose the order of work and [model routing](model-routing.md) to assign responsibilities. Lock cuts and refresh their timing before final visual production; preliminary source discovery may overlap candidate-cut preparation.

## A practical session

1. **Prepare locally.** Read the existing snapshot, timed transcript, source ledger, and receipts. Refresh live state once at the start of an editing batch. Generate a compact scene index and only the packets needed for this request. Use code for arithmetic, media probing, file search, deduplication, and frame/subtitle mapping.
2. **Make editorial decisions once.** A capable model sets the narrative, protected moments, acceptable cuts, visual beats, and quality checklist. Save decisions in files. A second harness consumes that plan rather than asking the creator to explain the video again.
3. **Overlap independent preparation.** At most two workers initially: one handles missing proof sources, another prepares approved assets or reel candidates. Give each a disjoint assignment, a bounded packet, and an output file. They do not both read the whole project. Do not launch extra Claude workers on the same allowance just to make the screen look busy.
4. **Use the available plan intelligently.** Codex or Grok Build can run the same local scripts and prepare the same assets. Keep a strong editorial reviewer when its judgment improves the result. Move routine work between authorized plans through the job folder. Check the actual usage meter; a different session on the same account is still the same allowance. Do not silently switch to API billing or purchase more quota.
5. **Apply one coherent batch.** One writer stages the change, checks the project-wide diff and rendered boundaries, then commits against the live base hash. Cached context saves preparation; it does not replace conflict checks. If the creator is editing, continue independent preparation instead of fighting the timeline.
6. **Render only approved changes.** Reuse the established templates. First check a still, then a short low-resolution motion preview, then the final render. A change to one source label should invalidate that visual and its dependent export, not every section in the video.
7. **Finish and reuse.** Review the real exported video and audio. Derive reels from the accepted story/source map, keeping the existing proof research and corrected transcript. Save final decisions, files, hashes, pending issues, and next action so another harness can resume with a small packet.

## What to avoid

- Feeding the entire transcript, proof README, equivalent proof JSON, and tool history to every worker.
- Running three generic full-video critics when one reviewer plus targeted checks would answer the actual questions.
- Using a language model to poll rendering, count frames, or rediscover file paths.
- Starting high-resolution renders before the text, crop, and visual treatment are accepted.
- Assuming more workers means more allowance, or that a faster service tier consumes the same quota.
- Removing the final editorial/audio review to make the usage numbers look better.

## When to try a smaller model

Test it on one representative scene with the same sources and acceptance criteria. Compare accepted output, missing claims, bad cuts, visual mistakes, required corrections, total tokens/credits when measurable, and elapsed time. Keep the substitution only if quality holds and total effort falls. Use stronger models immediately for ambiguity, source contradictions, difficult timing, or repeated failure. Current model names and prices belong in the service reference, not in an unchangeable routing rule.

If a plan runs out, checkpoint once and hand off to an authorized available harness. Keep the source ledger and accepted decisions; do not restart research. If no capacity remains, report the exact unfinished stage. Repeated retries against an exhausted allowance do not advance the edit.
