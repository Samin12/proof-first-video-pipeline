# Local job protocol

The stdlib `scripts/run.py` stores state and creates an **advisory task manifest**. It does not call models, spend money, dispatch workers, mutate Borumi, or perform visual review. The current harness executes tasks from the manifest. Read the help for the installed version if a field differs. New jobs use the staged version-2 graph; existing version-1 jobs retain their original graph and are never silently migrated.

## First run and resume

```bash
python3 <skill>/scripts/run.py init '<job>' \
  --goal 'Tighten the opening scene and preserve its proof' \
  --mode fast --scene '<scene ID>' --plan-only --max-workers 2 --budget-usd 0
python3 <skill>/scripts/run.py ingest '<job>' \
  --snapshot '<saved snapshot.json>' --transcript '<saved transcript directory>'
python3 <skill>/scripts/run.py next '<job>'
```

Use `--plan-only` when asked to prepare or propose without applying: all modes then stop at the assembled plan/handoff. `tasks <job> --plan-only` adds this boundary to an existing job. Only an explicitly authorized `tasks <job> --execute` clears it; the command schedules execution tasks but never performs them.

Modes: `fast` prepares cuts without mandatory research or new visual production; `proof` overlaps cut candidates and preliminary source discovery, then gates timed visuals on committed cuts and post-cut timings; `reel` plans clips and a local render, with no timeline writer. Specify repeated `--scene` flags for a bounded edit. Without a scene restriction, all substantive narration scenes participate. Chapter cards and sub-frame remnants remain in structural/coverage review without automatically spawning their own workers.

View the actual graph, including readiness and model tiers:

```bash
python3 <skill>/scripts/run.py pipeline '<job>' --format mermaid
python3 <skill>/scripts/run.py pipeline '<job>' --format json
```

The Mermaid output can be pasted into a Markdown Mermaid fence. The [interactive map](../assets/pipeline/index.html) is a generic explanation; the command above reads the current job. Neither launches workers. Model tiers and tool assignments tell the harness how to dispatch, not which model it actually selected.

## Keep baseline and post-cut timings distinct

Version 2 stores immutable stage captures under `stages/<stage>/<digest>/`. Keep the original baseline for cut planning; do not replace it with a post-cut snapshot simply to refresh visual timing.

1. Ingest the source snapshot and timed words with the default `--stage baseline`.
2. Complete the reviewed cut and its checked writer task. The writer receipt must include `timeline_hash_after` and an `evidence.readback` artifact with a matching `timeline_hash` (or the upstream snapshot's `hash`). The artifact must be included in `artifacts` and is hash-bound like all other evidence.
3. Export the real committed project's fresh snapshot and transcript. Ingest them with `--stage postcut`:

```bash
python3 <skill>/scripts/run.py ingest '<job>' --stage postcut \
  --snapshot '<postcut snapshot.json>' --transcript '<postcut timed transcript directory>'
```

The post-cut hash must match the recorded writer readback. This refreshes downstream timings without invalidating the completed baseline cut. Post-cut inputs are not a substitute for the next writer's live conflict check. If the project changed independently, inspect it and reopen/replan the affected work; do not relabel a changed snapshot to force a match.

After this ingest, reread `tasks.json` or `next`: the `postcut-timings` task's input digest now includes the imported capture. Build its completion receipt with that current digest and set `evidence.postcut_index` to the immutable index path returned for the stage. Include that index in `artifacts`.

New cuts invalidate dependent proof placement, final captions/audio mapping, previews and exports. Old research artifacts and receipts remain available for deliberate reuse; the coordinator still checks whether they support the retained claims. Replacing the baseline after a committed cut is rejected until the affected work is explicitly reopened.

## Dispatch and resume

Inputs may be the original `snapshot.py` JSON or a `dump_transcript.py` work directory. Timed words must be in **project milliseconds**. The runner rejects raw SQLite input and unsupported time formats. The upstream snapshot CLI's global `--work` and `--project-id` options must precede `save`; see [Borumi](borumi.md).

The job stores `goal.md`, `job.json`, `checkpoint.json`, `scene-index.json`, `tasks.json`, scene packets, source assets, outputs, and receipts. Full local source artifacts stay outside model prompts. Research packets contain short timed passages; planning packets retain exact word/segment data. A single unusually long scene may still need a smaller task slice.

`next` returns at most the configured worker count of ready tasks. It **does not reserve a task** or enforce active-worker concurrency. One coordinator owns dispatch and records active tasks; do not have two harnesses call `next` and launch the same work. Shared file locks protect file writes, not the entire human/agent workflow. Workers return a bounded JSON result plus relevant artifact paths; one coordinator records completion.

On resume:

```bash
python3 <skill>/scripts/run.py verify '<job>'
python3 <skill>/scripts/run.py next '<job>'
```

Capture live state before resuming actual timeline writes. Re-ingest if it changed. Unchanged input keeps valid work; changed scene inputs invalidate the affected tasks and downstream assembly/write/review tasks. Modified or missing completed artifacts cause a failure rather than silent reuse. Rebuild only affected work. Do not edit task manifests by hand to bypass this checking.

Change scope deliberately:

```bash
python3 <skill>/scripts/run.py tasks '<job>' --mode proof --scene '<scene ID>'
python3 <skill>/scripts/run.py tasks '<job>' --mode fast --all-scenes
```

## Results and completion records

Task result content should state decisions, exact ranges or claims, artifact paths, and unresolved questions. A minimal completion receipt uses the **actual** task ID and digest from `tasks.json`:

```json
{
  "task_id": "cut-candidates-s0001",
  "input_digest": "copy the complete digest from the current manifest",
  "status": "done",
  "summary": "Prepared the requested scene edit; no timeline change yet.",
  "artifacts": ["outputs/scene-plan.json"],
  "unresolved": [],
  "evidence": {}
}
```

```bash
python3 <skill>/scripts/run.py complete '<job>' --task '<ID>' --receipt '<receipt.json>'
```

IDs are generated from actual scene keys; the example is illustrative. Artifacts must exist inside the job. Writer/final tasks require evidence keys listed in their manifest. The runner hashes those files and the receipt; it does not determine whether their contents prove the worker's claims. A proposed write is not a completed writer task. In a plan-only job, use `status: "prepared"` with the honest `unresolved` list to record a useful handoff that still needs checks before execution. Prepared milestones do not unlock execution when the job is switched with `--execute`; they must be resolved. Keep `status: "done"` only for actually complete work. Record unresolved issues as pending work rather than submitting a false success receipt.

## Revise a completed milestone

Use `run.py reopen <job> --task <ID> --reason "What needs revision"`. It invalidates that milestone and its dependents, retains independent work, and records the reason while preserving old receipts. Write revised output to a new versioned path, such as `outputs/plan-s0001.v2.json`, then submit its new receipt. Do not edit checkpoint files or overwrite accepted artifacts to bypass integrity checks.

## Source cache

```bash
python3 <skill>/scripts/run.py asset '<job>' '<capture.png>' \
  --kind capture --url 'https://example.org/original' --claim 'What it supports' \
  --rights 'Creator capture; review intended use'
python3 <skill>/scripts/run.py cache '<job>' --url 'https://example.org/original' --max-age-hours 24
```

Files are copied into a content-addressed local cache. Freshness by age and hash integrity are separate from factual verification and reuse rights. Generated files must be marked `--kind generated`; never promote them to proof just because the hash is valid. Treat a public source that changed since capture as a new revision. Never commit real cache folders to the skill repository.

## Explicit cost arithmetic

`estimate` takes usage and supplied rates; it cannot read account quota or predict a plan's five-hour usage. `input_tokens` includes cached input; `output_tokens` must include billed reasoning. Rates and units must match the chosen provider/context tier/speed. Express paid cache writes, media generations, search items, and other line items through `tools`, using actual units. Keep non-USD credits separately unless the provider supplies a valid conversion.

```json
{"entries":[{"model":"chosen-model","input_tokens":20000,"cached_input_tokens":5000,"output_tokens":2000,"tools":[{"name":"search-items","units":10}]}]}
```

```json
{
  "as_of":"YYYY-MM-DD",
  "source_urls":["https://provider.example/pricing"],
  "models":{"chosen-model":{"input_per_million":"2","cached_input_per_million":"0.5","output_per_million":"6"}},
  "tools":{"search-items":{"per_unit":"0.005"}}
}
```

The rates above are a **schema example**, not a live quote. Run:

```bash
python3 <skill>/scripts/run.py estimate '<job>' --usage '<usage.json>' --rates '<rates.json>'
```

The result covers only supplied usage and is not a cumulative budget guard or spending authorization. The coordinator must maintain actual cumulative spend and check remaining authorized capacity before every paid submission. Missing prices fail instead of being treated as free. See [services](services.md) for dated real examples and billing distinctions.
