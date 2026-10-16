---
name: video-edit-pipeline
description: Run a staged Borumi video edit with an explicit cut-before-visuals pipeline, model roles, reusable proof assets and resumable jobs. Use when the user requests video-edit-pipeline or this staged workflow in Codex, Claude Code, Grok Build or another local harness. This separate skill preserves existing working editing skills.
---

# Video Edit Pipeline

Finish the requested edit at the established quality with the smallest useful context and existing tools. Optimize subscription usage and elapsed time before chasing lower token prices. Preserve the creator's meaning and established style. This is a separate fork of `video-edit-fast`, using the pinned `proof-first-video-editor` writers. Preserve both existing skills and their installations. No proprietary Workflow API is required.

## Start with the actual job

Read the project's saved checkpoint before inspecting it again. Identify the exact project, deliverable, existing raw backup, available local tools, and billing route. Reuse the user's current authorization and preferences. If no spending budget was given, use existing authorized plan capacity and local tools, with **$0 extra paid jobs**. Available credits are not unlimited permission to spend them.

Choose the smallest scope that fulfills the request:

- **Quick:** remove retakes, improve pacing, fix specified captions/layouts, export. Research only claims the edit adds or changes.
- **Proof:** full narrative cut, claim-to-source map, verified captures, chapter cards, visual placement, audio/caption pass, export.
- **Reel:** select self-contained moments from a reviewed master; reuse its sources and transcript, reframe, remap captions, render vertically.
- **Resume:** compare the live timeline with the checkpoint and invalidate affected work. Do not rerun valid research or renders.

On first use, read [setup and harnesses](references/harnesses.md). Run `python3 <skill>/scripts/run.py doctor`. Use [Borumi operations](references/borumi.md) for actual editor access and writes; use [the job protocol](references/jobs.md) for the helper commands.

For a full edit, follow [the visual pipeline](references/pipeline.md): cut candidates and source discovery → capable editorial cut review → one checked cut write → post-cut timings → retained proof and finishing → visuals → final export review → optional reels. Read [model roles](references/model-routing.md) when assigning workers and [starter scenarios](references/scenarios.md) when beginning from raw footage and a finished style reference. Timed visuals and final captions use the committed post-cut timeline, never the original timings.

## Plan once; send small packets

For preparation without execution, use `--plan-only`; retain unresolved findings in a prepared receipt. Create a local job folder outside the skill/repository. Save the outcome, allowed spend, model/billing route, timeline hash, scene index, and artifact paths there. Use `run.py init`, `ingest`, and `next`. Raw transcripts, media, receipts, and account details stay local.

Give a worker only its scene packet, exact question, source IDs, output schema, and relevant reference. Share files and hashes, not conversation histories. Run deterministic extraction, timing arithmetic, deduplication, subtitle mapping, rendering, and checks in scripts.

For independent research or planning, use up to two workers initially; tune to the account's measured capacity. No nested fan-out by default. One coordinator integrates their results; **one writer owns the Borumi timeline**. Use the harness's native subagents when available and authorized, or run the same tasks sequentially. Never claim that parallelism reduces total token use. Separate concurrency from model choice; skill frontmatter does not enforce either.

Choose effort per role using [model routing](references/model-routing.md): high for capable planning/decision gates, medium for routine execution, model-specific settings for small workers. Set and record each worker's actual model and effort explicitly. Fan-out alone does not justify maximum effort or automatic inheritance of the coordinator's settings.

Keep a capable model for editorial decisions and final review. Eliminate redundant context, calls, and renders first. Use a smaller model for extraction, claim classification, caption-name candidates, and source ranking only after it passes the same acceptance checks. Read [quota-efficient scheduling](references/quota-workflow.md) when optimizing a recurring workflow. Escalate ambiguous cuts, conflicting evidence, timing/crop failures, and final editorial judgment. Check [services and billing](references/services.md) before choosing a provider; record the route actually used. A goal tool helps only when supported and requested; the job's `goal.md` works everywhere. Stop repeated failures after two attempts, checkpoint, then change method or report the specific blocker.

## Research and production

Read [proof and media](references/proof-and-media.md) when adding resources, tweets, generated images, or video. The chain is **spoken claim → canonical source → captured evidence → timed visual → rendered check**. A search result is a lead. A generated scene is illustration. Neither is independent proof. Flag unsupported claims with timestamps; never silently rewrite their meaning.

Reuse verified captures, styles, and renders by content hash. Recheck time-sensitive facts and changed source pages. Read [visuals and reels](references/visuals-and-reels.md) only for that work. Show important evidence clearly; a static real screenshot with a crop/highlight often needs no generative service. Preview before a full-resolution render.

Before any timeline write, confirm the target and raw backup, read live state, stage a transaction with the inherited writer, inspect its diff and frames, and commit only if its base hash still matches. On collision, reread and replan. Never rewrite `.bmproj` directly. Preserve other people's edits and the source recordings.

## Verify the deliverable

Check the changed boundaries, layer order, evidence readability, audio joins/sync, caption names/timing, and final dimensions/duration. Review the exported artifact, including start/end and every changed region; a full proof edit additionally needs continuous playback review. [QA](references/qa.md) defines the evidence. A helper's passing checks do not prove visual/editorial quality.

Record the final file hashes, review evidence, unresolved issues, actual usage when available, and next action. Deliver the video and sidecars with a short factual report. Do not equate a queued render, successful API call, or draft with a finished export. Uploading or publishing videos requires the user's instruction; creating this skill does not authorize those actions.
