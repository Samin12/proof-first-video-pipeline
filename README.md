# Video Edit Pipeline

A separate staged-production skill for **Codex, Grok Build, Claude Code, and other local agent harnesses**: cut first, verify the retained claims, build timed visuals, finish and review, then derive reels. **Quality stays the acceptance gate; subscription usage and waiting are the optimization targets.**

This is a new fork of [video-edit-fast](https://github.com/Samin12/proof-first-video-editor-portable), built on the pinned writers from [proof-first-video-editor](https://github.com/Samin12/proof-first-video-editor). **Both working skills remain separate and unchanged.** Installation uses the new name `video-edit-pipeline` and its own toolchain configuration. No provider settings or original videos are replaced.

## See the pipeline

[Open the interactive pipeline](https://samin12.github.io/proof-first-video-pipeline/) · [Stage-by-stage guide](skills/video-edit-pipeline/references/pipeline.md) · [Model responsibilities](skills/video-edit-pipeline/references/model-routing.md) · [Example editing prompts](#example-prompts-for-editing-a-video)

The interactive map also ships at `skills/video-edit-pipeline/assets/pipeline/index.html` and opens offline. Select a stage to see its model tier, tools, inputs, output and quality gate. It is a reference map, not a live dashboard or a model launcher.

```mermaid
flowchart TD
    A[Snapshot and reusable assets · local] --> B[Cut candidates · small model]
    A --> C[Source discovery · small model]
    B --> D[Cut review and decision · capable model]
    C --> D
    D --> E[One writer applies cuts and saves post-cut timings]
    E --> F[Retained proof and visual plan]
    E --> G[Audio, captions and chapters]
    F --> H[Template visuals and short previews]
    H --> I[One writer assembles]
    G --> I
    I --> J[Final export and capable review]
    J --> K[Optional reels from reviewed master]
```

## Recommended kickoff: model, effort, and team

For raw footage plus a finished style reference, start with a capable coordinator at **High effort**. In Codex, the starting recommendation is **GPT-6.1 Sol · High effort · Standard speed**. Check the first representative section against the reference before scaling the treatment to the full video.

| Harness | Coordinator | Preparation workers | Escalation |
|---|---|---|---|
| Codex | **GPT-6.1 Sol · High** for story/cut planning and acceptance reviews; **Medium** for routine execution | **GPT-6 Luna · High** for multi-tool scouting; **Low** for simple extraction | **GPT-6 Astra · Medium** initially; raise effort for the specific unresolved problem |
| Claude Code | **Sonnet 5.5 · High** for planning and acceptance reviews; **Medium** for routine execution | **Haiku 5.5 · Medium** for bounded cut/source proposals and caption findings | **Opus 5.5 · Medium** initially; raise effort for the specific unresolved problem |
| Grok Build | **Grok 4.7 · High** for lead decisions/review; **Medium** for bounded execution | An available suitable model at **Medium**; **Low** only for simple checks | **High**, then **xhigh** for a specific unresolved hard task; no `max` setting |

High effort helps reconcile the story, reference style, factual risks, and task dependencies. Once that plan exists, dispatching workers and applying reviewed instructions are routine. If the host cannot switch coordinator effort cleanly, leave it High; the user does not need to babysit phase changes. Set each worker's model **and** effort explicitly, verify the resolved settings, and record any fallback. A small model may need high effort for reliable multi-tool work. Effort scales and subscription usage differ across providers.

Use **one coordinator and at most two active preparation workers** initially. Reuse the worker slots between stages. The coordinator can also own the timeline; one writer means one responsibility, not an extra permanent agent.

| Responsibility | Assignment and boundary |
|---|---|
| Propose retake cuts, repetitions, source leads, or caption defects | Small worker; one scene/claim packet; returns candidates and uncertainty; does not make final deletions |
| Decide narrative cuts and accept factual proof | Capable coordinator at High effort; inspect context and actual evidence |
| Fill an approved visual template | Bounded worker; capable reviewer accepts the preview; new layout/animation code goes to a capable model |
| Apply cuts or place visuals | One timeline owner using the checked Borumi scripts, live state and readback |
| Timing, hashes, subtitle mapping, rendering and technical checks | Local scripts; no separate model needed for the computation |
| Final editorial/audio/visual review | Capable model at High effort with actual playback tools; escalate unresolved hard decisions |

These recommendations were checked **2026-10-16** and are starting points, not a cross-model quality benchmark. Model labels in the skill do not configure the harness automatically. [Official sources, effort details and runtime configuration](skills/video-edit-pipeline/references/model-routing.md).

## Install and use

[Download the skill ZIP](https://github.com/Samin12/proof-first-video-pipeline/releases/latest/download/video-edit-pipeline.zip) and extract its `video-edit-pipeline` folder into `~/.agents/skills/`, or use the clone-based installer below. The downloaded folder includes the same setup script; run its `scripts/setup.py fetch` once before Borumi editing.

```bash
git clone https://github.com/Samin12/proof-first-video-pipeline.git
cd proof-first-video-pipeline
python3 skills/video-edit-pipeline/scripts/setup.py install
python3 skills/video-edit-pipeline/scripts/setup.py fetch
python3 skills/video-edit-pipeline/scripts/run.py doctor
```

The skill is linked into `~/.agents/skills/video-edit-pipeline`, a shared location supported by Codex and Grok Build. Keep the checkout and refresh/restart skill discovery. The fetch step gets pinned public dependencies into an isolated directory; it preserves existing installations and video projects.

For **Claude Code**, run `setup.py install --harness claude`, then use `/video-edit-pipeline`. Other local harnesses can read [SKILL.md](skills/video-edit-pipeline/SKILL.md) and use the same scripts. A browser chat without access to the Mac can prepare research/plans but cannot directly edit local Borumi. [Harness setup and compatibility](skills/video-edit-pipeline/references/harnesses.md).

## Example prompts for editing a video

**Trying this on a video you already edited? Start with example 1.** It creates a separate revision for comparison. Example 2 tests a fresh edit from the original raw project against your finished reference.

Select the [coordinator model and effort](#recommended-kickoff-model-effort-and-team) above. Replace bracketed text with your actual project names, paths or instructions. These prompts use Codex's **`$video-edit-pipeline`**; in Claude Code or Grok Build, change the first line to **`/video-edit-pipeline`**. Keep the same brief and review criteria across harnesses.

### 1. Test the pipeline on an already-edited video

Use this for the first trial. The existing finished edit is the baseline, and the new copy is the candidate. This measures the quality of a revision; a raw-to-finished trial measures the full editing workflow.

```text
$video-edit-pipeline

Test this pipeline on my already-edited Borumi project “[PROJECT NAME]”.
Locate and verify the project. Preserve it as the baseline and create a
separate working copy named “[PROJECT NAME] — pipeline test”. Inspect the
existing edit, transcript and proof assets before deciding what to change.

Improve pacing, clarity, proof readability, captions and audio only where
there is a concrete benefit. Preserve my meaning, voice and established
visual style. Keep good existing edits and visuals. Do not rebuild them
just to exercise every pipeline stage.

Start with one representative scene, aiming for a 30–60-second comparison.
Use a separate scene-scoped pilot job and protect the rest of the timeline.
Save matching baseline and candidate previews, using the same source passage
even if their edited durations differ. Have the capable coordinator watch
and hear both. If the candidate passes the same quality bar, continue with
the accepted treatment in a fresh full-job snapshot of the working copy.
If it does not, keep the baseline treatment and report the specific issue.

Use the skill's model/effort table: High coordinator effort for planning,
editorial decisions and review; Medium for routine execution when supported.
Use at most two bounded preparation workers, explicitly setting and checking
their actual models and effort. Keep one timeline writer. Reuse existing
research, captures and templates; research only new, changed or stale claims.
Apply any cuts before refreshing timings and placing affected visuals.

Deliver the reviewed candidate export and a before/after comparison with
timestamps: what changed, what improved, any regressions and unresolved issues.
Record elapsed time, models/effort, retries and actual usage-meter readings
when available; mark unavailable usage as unknown. Save the job folder so
another harness can resume. Use existing authorized capacity; no extra paid
API/generation jobs without an agreed budget. Do not upload or publish.
```

<a id="raw-to-finished-starter-prompt"></a>

### 2. Raw-to-finished starter prompt

```text
$video-edit-pipeline

Use “[RAW PROJECT]” as the Borumi source and the current finished “[REFERENCE]”
as the style and quality reference. Locate and verify both. Create a separate
working copy; preserve the originals and existing working skills.

Start with a representative 30–60-second section in a scene-scoped pilot job.
Match the reference's pacing, real proof visuals, camera layout, captions and
audio quality. After that treatment passes review, continue the full video
from a fresh working-copy snapshot and reuse the accepted pilot assets.

Use High coordinator effort for planning, cut decisions and final review;
Medium for routine execution when supported. Use at most two preparation
workers with the skill's model-specific effort settings. Verify each worker's
actual model and effort, and report unsupported settings or fallbacks.

Prepare cut candidates and source leads in parallel. Review and apply cuts,
then refresh timings before producing visuals for the retained claims.
Keep one timeline writer. Reuse research, real screenshots/tweets, templates
and timed transcripts. Use local code for timing, captions and rendering.

Save checkpoints. Deliver the reviewed master, corrected captions, chapters,
source ledger and review evidence. Use existing authorized tools/capacity;
do not add paid API or generation jobs without an agreed budget.
Flag unsupported claims. Do not upload or publish the video.
```

The runner scopes by scene, so the coordinator must select a real scene ID for the pilot; an unscoped job prepares the whole video. [Exact pilot commands, preparation-only mode, reels, and cross-harness resume prompts](skills/video-edit-pipeline/references/scenarios.md).

### 3. Make one specific improvement

Use this when you already know what needs fixing. Replace the example change with your own request.

```text
$video-edit-pipeline

Open the edited Borumi project “[PROJECT NAME]” and make a separate working
copy named “[PROJECT NAME] — targeted fix”. Change only this:
[Example: tighten the repeated explanation in scene 3 and enlarge the tweet
so its evidence is readable. Preserve the rest of the video.]

Use the smallest applicable workflow. Reuse the existing transcript, sources,
captures and visual treatment. Use one coordinator; add a bounded worker only
if independent preparation will help. Use the skill's recommended model/effort
settings. Keep one timeline writer. If cuts change timing, refresh it before
updating the affected visuals and captions.

Review the changed passage and its joins with the surrounding footage.
Export the revised video, give me a before/after preview of the changed area,
and list the exact changes and any unresolved issue. Save a checkpoint.
Use existing authorized capacity; no extra paid API/generation jobs without
an agreed budget. Do not upload or publish.
```

### 4. Make a reel from the finished video

```text
$video-edit-pipeline

Use the reviewed finished video at “[MASTER PATH]” and its Borumi project
“[PROJECT NAME]”. Create a separate reel job; preserve the master and project.
Find three self-contained 30–60-second moments and render the strongest one
as a 1080x1920 reel. Keep the speaker's meaning and include a clear payoff.

Reuse the existing transcript, verified proof and visual style. Use original
camera/screen layers when available; keep the speaker, captions and evidence
readable on a phone. Flag a framing limitation if only a flattened master is
available. Research only new or changed claims. Use the skill's model/effort
settings, local timing/render tools and at most two preparation workers.

Review the actual export for pacing, crop, captions, evidence and audio sync.
Deliver the reel, its source ranges and a short explanation of the selection.
Save the job and review evidence. Use existing authorized capacity; no extra
paid API/generation jobs without an agreed budget. Do not upload or publish.
```

### 5. Resume in Codex, Claude or Grok after a usage limit

```text
$video-edit-pipeline

Resume the video edit saved at “[JOB FOLDER]”. Read the goal, checkpoint,
pipeline state and unresolved findings. Verify the current Borumi project
and saved artifact hashes. Continue only ready or invalidated work, reusing
accepted cuts, sources, templates and renders whose inputs still match.

Use this harness's supported models and effort settings for the recorded
roles. Report actual assignments and fallbacks. Keep at most two preparation
workers and one timeline writer. Preserve the original project, reference
and current working copy. Keep the job's existing scope and spending limits.
Finish its requested deliverable and review; do not upload or publish.
```

For a **preparation-only trial**, append this to example 1 or 2: “Use `--plan-only`. Return the proposed cuts, proof gaps, visual treatment and model assignments. Stop before timeline writes, generation or rendering.” A plan-only result is a proposal; compare actual exports to judge video quality.

For a **cross-model comparison**, run example 1 or 2 from the same untouched baseline in a separate working copy and job folder per harness. Use the same source passage, brief and quality criteria. Record whether each run had a warm asset cache, along with wall time, correction rounds and available usage readings. Compare pacing, meaning, evidence readability, caption accuracy and audio sync. Keep raw-to-finished results separate from revision results, and report unknown usage without estimating a savings percentage.

## How this saves time and usage

| Work | Default route |
|---|---|
| Inventory, timing, hashes, subtitles, render preparation | Local deterministic scripts |
| Simple extraction and candidate selection | One scene packet; smaller model only after quality checks |
| Story, ambiguous edits, final judgment | Balanced/strong model only where needed |
| Research | Existing source cache first; targeted search/capture for missing claims |
| Visuals | Reusable local templates; real source captures |
| Generated shots | Optional Higgsfield or another verified provider within a set budget |
| Parallelism | Two independent workers initially; one Borumi writer |
| Continuation | Saved goal, scene state, artifacts and hash-checked receipts |

Choose **fast** for targeted cuts, **proof** for full evidence-led production, and **reel** for vertical derivatives. Existing timed transcripts are reused. Completed sources and renders are reused when their inputs remain valid. A small edit does not trigger an entire audio/research/visual pipeline.

Parallelism reduces waiting only where tasks are independent; it does not create more subscription allowance. The priority is to reduce consumed plan capacity per accepted edit, not to choose the cheapest model at any cost. Optional extra paid jobs default to **$0** until a budget is supplied; that setting is a billing guard, not the quality target. Model speed modes and API authentication can change which allowance or bill is used.

Start with the [pipeline](skills/video-edit-pipeline/references/pipeline.md) and [raw-to-finished prompt](skills/video-edit-pipeline/references/scenarios.md). Read the [quota workflow](skills/video-edit-pipeline/references/quota-workflow.md) and [service research](research/services-and-costs.md) as needed. Example API arithmetic is not a promise about subscription usage or video quality.

## What's included

- [The skill](skills/video-edit-pipeline/SKILL.md), with references loaded only for the active stage.
- `run.py`: staged dependency graph, model-role metadata, mode/scoped packets, resumable receipts, content cache, and explicit cost arithmetic.
- `setup.py`: install, isolated pinned toolchain, and correctly configured calls to existing Borumi scripts.
- `reel.py`: frame-mapped rough reels and optional SRT remapping from a reviewed local master.
- [Styled reel template](skills/video-edit-pipeline/assets/reel-template/): reusable local composition for camera/proof cards, captions, progress, and CTA.
- [Borumi study](research/borumi-patterns.md) and [validation record](research/validation.md).

The job runner is a state helper, **not an autonomous model scheduler or a hard spending limiter**. Your harness carries out its ready tasks. Structural checks are not visual QA; the final export must be watched and heard. [Job protocol](skills/video-edit-pipeline/references/jobs.md), [QA](skills/video-edit-pipeline/references/qa.md).

## Requirements and boundaries

Python 3.9+ for helpers; FFmpeg/ffprobe for media; macOS with Borumi and MCP enabled for timeline edits. The inherited writers need their documented image/audio dependencies. Styled motion uses Remotion and the existing animation kit; install that only when needed. Service connections and authentication are configured separately in each harness.

The isolated legacy bridge is patched to decline automatic consent prompts and uses port 47813. Timeline changes still go through a backup, staged transaction, live hash check, frame inspection, and committed readback. No private footage, transcripts, screenshots, account data, or credentials are included in this repository. The skill does not publish your videos automatically.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 skills/video-edit-pipeline/scripts/run.py --help
```

Exact measured validation and remaining limits are in [validation.md](research/validation.md). Lower-cost model quality equivalence has not been established by a controlled full-video benchmark.

MIT. Builds on Samin Yasar's [proof-first-video-editor](https://github.com/Samin12/proof-first-video-editor), [edit-borumi-video](https://github.com/Samin12/edit-borumi-video), and [opencutagent-borumi](https://github.com/Samin12/opencutagent-borumi).
