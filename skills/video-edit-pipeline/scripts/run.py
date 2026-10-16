#!/usr/bin/env python3
"""Local, stdlib-only job ledger. No model calls, paid requests, or timeline writes.

Inputs: original proof-first snapshot.py JSON; or dump_transcript.py's WORK
directory (scenes.json, overview.json/timeline_summary.json, optional transcript/).
All transcript times MUST be project milliseconds, not source-media timestamps.
New jobs use graph_version 2; versionless jobs retain the legacy graph. V2 keeps
immutable baseline/postcut captures: ingest JOB --stage postcut requires a done
write-cut receipt with timeline_hash_after and a matching evidence.readback JSON
artifact. Its timeline_hash (or upstream snapshot hash) must match the new capture.
pipeline JOB --format mermaid prints the actual graph as plain Mermaid text.

For a plan/handoff without execution, use init JOB --goal TEXT --plan-only.
This persists in job.json and omits writer, renderer, and final-export-review
tasks in every mode. tasks JOB --plan-only applies the same stop to an existing
job. Only tasks JOB --execute clears it; that command includes execution tasks
in the manifest but does not run them. Goal prose is never parsed for permission.

Receipt JSON: {"task_id":"research-s0001", "input_digest":"...", "status":"done",
 "summary":"...", "artifacts":["outputs/research-s0001.json"], "unresolved":[]}
Artifacts are paths relative to JOB. Timeline and final-review receipts also need
an evidence object mapping the named checks in tasks.json to artifact paths.
Receipts record a worker's assertions; this program does not certify their truth.
In a plan-only job, status "prepared" may include unresolved string findings.
It checkpoints an honest handoff, not a finished edit. tasks --execute discards
prepared milestones and their dependents; resolve findings before recording done.
To revise a handoff, use reopen JOB --task ID --reason TEXT. This invalidates
that checkpoint and its dependents, preserving independent work and historic
receipt files. Write revised artifacts to new paths (e.g. outputs/plan.v2.json),
then complete the reopened tasks with new receipts; do not overwrite v1 files.

Usage JSON: {"entries":[{"model":"example", "input_tokens":1000,
 "cached_input_tokens":200, "output_tokens":100,
 "tools":[{"name":"search", "units":2}]}]}
input_tokens INCLUDES cached_input_tokens. Rates JSON (USD, supplied by you):
{"models":{"example":{"input_per_million":"1", "cached_input_per_million":"0.1",
 "output_per_million":"5"}}, "tools":{"search":{"per_unit":"0.01"}}}
Examples above are illustrative arithmetic only, not provider prices. Explicit
zero rates are accepted; missing rates for nonzero usage are errors. Include
billable reasoning tokens in output_tokens and tool-result tokens in input_tokens.
Represent provider cache-write premiums or video-generation charges as explicit
tools[] entries with measured billable units and per-unit USD rates. Credit counts
are not dollars: supply the actual purchased/effective USD rate, never guess it.
Estimates do not measure subscription usage or grant authorization to spend.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import urlsplit

VERSION = 1
CATEGORIES = ("layouts", "overlays", "content", "controls")


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(Invalid("Nonfinite JSON: " + x)))


def write(path, value, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=None if compact else 2,
                      separators=(",", ":") if compact else None, ensure_ascii=False, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def inside(job, relative):
    p = Path(relative)
    require(not p.is_absolute(), "Expected a relative job path: " + str(relative))
    out = (job / p).resolve()
    require(out != job and job in out.parents, "Path escapes job: " + str(relative))
    return out


def job_at(value):
    job = Path(value).expanduser().resolve()
    require((job / "job.json").is_file(), "Not a job; run init first: " + str(job))
    return job


@contextmanager
def locked(job):
    lock = job / ".run.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise Invalid("Job writer is locked. If its process crashed, inspect then remove " + str(lock))
    try:
        (lock / "owner").write_text(str(os.getpid()), encoding="utf-8")
        yield
    finally:
        (lock / "owner").unlink(missing_ok=True)
        lock.rmdir()


def decimal(value, label):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Invalid(label + " must be a nonnegative finite number")
    require(d.is_finite() and d >= 0, label + " must be a nonnegative finite number")
    return d


def time_ms(value, label):
    require(not isinstance(value, bool) and isinstance(value, (int, float)) and
            math.isfinite(value) and value >= 0, label + " must be nonnegative finite milliseconds")
    return value


def count(value, label):
    require(type(value) is int and value >= 0, label + " must be a nonnegative integer")
    return value


def parse_date(value):
    require(isinstance(value, str), "captured_at must be ISO-8601 text with timezone")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Invalid("Invalid ISO-8601 captured_at")
    require(dt.tzinfo is not None, "captured_at needs a timezone")
    require(dt <= datetime.now(timezone.utc), "captured_at cannot be in the future")
    return dt


def paths(args):
    config_path = Path(os.environ.get("VIDEO_EDIT_PIPELINE_CONFIG", str(Path.home() / ".video-edit-pipeline" / "toolchain.json"))).expanduser()
    config = read(config_path) if config_path.is_file() else {}
    config = config.get("paths", config)
    defaults = {"edit_skill": "~/.borumi-edit/skill", "proof_skill": None,
                "animation_kit": "~/.borumi-agent/animation-kit"}
    envs = {"edit_skill": "BORUMI_EDIT_SKILL", "proof_skill": "PROOF_FIRST_SKILL",
            "animation_kit": "BORUMI_ANIMATION_KIT"}
    result = {}
    aliases = {"edit_skill": "edit", "proof_skill": "proof", "animation_kit": "animation_kit"}
    for key, default in defaults.items():
        value = getattr(args, key, None) or os.environ.get(envs[key]) or config.get(key) or config.get(aliases[key]) or default
        p = Path(value).expanduser().resolve() if value else None
        if key == "proof_skill" and p and (p / "plugins/proof-first-video-editor/skills/proof-first-video-editor").is_dir():
            p = p / "plugins/proof-first-video-editor/skills/proof-first-video-editor"
        result[key] = str(p) if p else None
    return result


def doctor(args):
    resolved = paths(args)
    expected = {"edit_skill": "scripts/applylib.py", "proof_skill": "scripts/borumi/snapshot.py",
                "animation_kit": "package.json"}
    deps = {k: {"path": v, "present": bool(v and (Path(v) / expected[k]).is_file())}
            for k, v in resolved.items()}
    return {"python": sys.version.split()[0], "offline_runner_ready": sys.version_info >= (3, 9),
            "dependencies": deps, "executables": {x: shutil.which(x) for x in ("ffmpeg", "ffprobe", "node", "uv")},
            "live_bridge_checked": False, "timeline_writer_ready": False,
            "note": "Presence only. Existing toolkit owns live bridge, backup, transaction and rendered-frame checks."}


def init(args):
    job = Path(args.job).expanduser().resolve()
    require(args.goal.strip(), "Goal cannot be empty")
    require(not job.exists() or not any(job.iterdir()), "init refuses a nonempty folder")
    budget = decimal(args.budget_usd, "budget_usd")
    require(1 <= args.max_workers <= 8, "max_workers must be 1..8 (2 is the default)")
    deps = paths(args)
    job.mkdir(parents=True, exist_ok=True)
    with locked(job):
        for name in ("inputs", "packets", "outputs", "receipts", "cache/objects"):
            (job / name).mkdir(parents=True, exist_ok=True)
        (job / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
        (job / "goal.md").write_text("# Video edit goal\n\n" + args.goal.strip() +
              "\n\nMode: " + args.mode + "\n\nAPI budget: $" + str(budget) +
              " USD. Budget is a cap, not an instruction to spend.\n\n" +
              "Execution scope is controlled by plan_only in job.json; true stops at the assembled plan/handoff.\n\n" +
              "Authoritative settings and current scope: job.json. Progress: checkpoint.json.\n",
              encoding="utf-8")
        write(job / "job.json", {"version": VERSION, "created_at": now(), "goal": args.goal,
              "budget_usd": str(budget), "max_workers": args.max_workers, "project_id": args.project_id,
              "mode": args.mode, "scene_scope": args.scene or [],
              "graph_version": args.graph_version,
              "plan_only": args.plan_only,
              "paths": deps, "policy": {"single_timeline_writer": True, "paid_calls_by_runner": False,
              "max_worker_revisions": 1, "full_review_required": True}})
        write(job / "checkpoint.json", {"version": VERSION, "input_digest": None, "completed": {}})
        write(job / "assets.json", {"version": VERSION, "entries": []})
    return {"job": str(job), "budget_usd": str(budget), "plan_only": args.plan_only, "next": "ingest", "paid_calls": 0}


def source_data(path):
    if path.is_file():
        require(path.suffix.lower() == ".json", "Use snapshot.py JSON or dump_transcript WORK directory; raw SQLite is not accepted")
        return read(path), None
    require(path.is_dir(), "Snapshot path does not exist")
    if (path / "snapshot.json").is_file():
        return read(path / "snapshot.json"), path / "transcript"
    scenes = read(path / "scenes.json")
    summary = read(path / "timeline_summary.json") if (path / "timeline_summary.json").is_file() else {}
    overview = read(path / "overview.json") if (path / "overview.json").is_file() else {}
    project = overview.get("project", {})
    data = {"duration_ms": summary.get("duration_ms", project.get("duration_ms")),
            "timeline_hash": summary.get("timeline_hash", project.get("timeline_hash")),
            "project_id": summary.get("project_id", project.get("id")),
            "scenes": scenes["scenes"], "layers": summary.get("layers", [])}
    if (path / "mic_segments.json").is_file():
        mic = read(path / "mic_segments.json")
        if data["timeline_hash"] and mic.get("timeline_hash"):
            require(data["timeline_hash"] == mic["timeline_hash"], "Export files have different timeline hashes; recapture")
        data["layers"] = mic.get("layers", data["layers"])
    return data, path / "transcript"


def normalize(data):
    require(isinstance(data, dict), "Snapshot must be a JSON object")
    duration = data.get("duration_ms", data.get("duration"))
    time_ms(duration, "duration")
    require(duration > 0, "Snapshot duration must be positive")
    scenes, ids = [], set()
    for s in data.get("scenes", []):
        if isinstance(s, (list, tuple)):
            require(len(s) == 4, "snapshot.py scene needs [id,name,start_ms,end_ms]")
            s = dict(zip(("id", "name", "start_ms", "end_ms"), s))
        require(isinstance(s, dict), "Scene must be an object or 4-item tuple")
        sid = s.get("id")
        require(isinstance(sid, str) and sid and sid not in ids, "Scene ids must be unique nonempty strings")
        a, b = time_ms(s.get("start_ms"), "scene start"), time_ms(s.get("end_ms"), "scene end")
        require(a < b <= duration + 1, "Scene interval is empty or exceeds duration: " + sid)
        ids.add(sid)
        out = {"id": sid, "name": s.get("display_name") or s.get("name") or sid, "start_ms": a, "end_ms": b}
        if isinstance(s.get("script"), str):
            out["script"] = s["script"]
        scenes.append(out)
    require(scenes, "Snapshot has no scenes")
    scenes.sort(key=lambda s: (s["start_ms"], s["id"]))
    for left, right in zip(scenes, scenes[1:]):
        require(left["end_ms"] <= right["start_ms"] + 1, "Scenes overlap; unsupported snapshot")
    segments = []
    for cat in CATEGORIES:
        for sid, v in data.get(cat, {}).items():
            require(isinstance(v, (list, tuple)) and len(v) >= (3 if cat == "layouts" else 5), "Invalid " + cat + " tuple")
            a, b = (v[0], v[1]) if cat == "layouts" else (v[1], v[2])
            segments.append({"id": sid, "kind": cat, "layer": "layout" if cat == "layouts" else v[0],
                             "start_ms": a, "end_ms": b, "data": list(v[2:] if cat == "layouts" else v[3:])})
    for layer in data.get("layers", []):
        for seg in layer.get("segments", []):
            segments.append({k: v for k, v in dict(seg, kind=layer.get("kind"), layer=layer.get("id")).items()
                             if k in ("id", "kind", "layer", "start_ms", "end_ms", "media", "group_id", "properties", "scene_id")})
    for s in segments:
        a, b = time_ms(s.get("start_ms"), "segment start"), time_ms(s.get("end_ms"), "segment end")
        require(a < b <= duration + 1, "Invalid segment interval")
    segments.sort(key=lambda s: (s["start_ms"], str(s.get("id", ""))))
    return {"duration_ms": duration, "timeline_hash": data.get("timeline_hash", data.get("hash")),
            "project_id": data.get("project_id"), "scenes": scenes, "segments": segments}


def transcript_words(path, timeline_hash):
    if path is None or not path.exists():
        return []
    files = sorted(path.glob("*words.json")) if path.is_dir() else [path]
    require(files or path.is_dir(), "No transcript files")
    words = []
    for file in files:
        data = read(file)
        if isinstance(data, dict) and data.get("timeline_hash") and timeline_hash:
            require(data["timeline_hash"] == timeline_hash, "Transcript timeline hash is stale: " + file.name)
        if isinstance(data, dict) and "layers" in data:
            raw = [w for layer in data["layers"] for seg in layer.get("segments", []) for w in seg.get("items", [])]
        else:
            raw = data.get("words", []) if isinstance(data, dict) else data
        require(isinstance(raw, list), "Transcript needs words[] or Borumi layers[].segments[].items[]")
        for w in raw:
            if isinstance(w, dict):
                require(all(k in w for k in ("start_ms", "end_ms", "text")), "Transcript dict words require start_ms, end_ms, text")
                w = [w["start_ms"], w["end_ms"], w["text"]]
            require(isinstance(w, list) and len(w) == 3 and isinstance(w[2], str), "Transcript words need [start_ms,end_ms,text]")
            a, b = time_ms(w[0], "word start"), time_ms(w[1], "word end")
            require(a <= b, "Word end precedes start")
            words.append((a, b, w[2]))
    return [list(w) for w in sorted(set(words))]


def packet_rows(normalized, words, prefix=""):
    """Canonical packets, shared by ingestion and integrity checking."""
    rows, packets = [], {}
    for no, scene in enumerate(normalized["scenes"], 1):
        key = "s%04d" % no
        a, b = scene["start_ms"], scene["end_ms"]
        sw = [w for w in words if a <= (w[0] + w[1]) / 2 < b]
        segs = [s for s in normalized["segments"] if s["start_ms"] < b and s["end_ms"] > a]
        compact_segments = []
        for s in segs:
            compact = {k: v for k, v in s.items() if k in ("id", "kind", "layer", "start_ms", "end_ms", "media", "group_id", "scene_id")}
            if s.get("kind") == "content" and s.get("data"):
                values = s["data"]
                compact["media"] = dict(zip(("media_id", "start_ms", "end_ms", "group_id"), values))
            compact_segments.append(compact)
        passages = []
        for w in sw:
            if not passages or w[0] - passages[-1][1] > 1200 or w[1] - passages[-1][0] > 15000:
                passages.append([w[0], w[1], w[2]])
            else:
                passages[-1][1] = max(passages[-1][1], w[1])
                passages[-1][2] += " " + w[2]
        research = {"version": VERSION, "scene_key": key, "scene": scene, "passages": passages, "word_count": len(sw),
                    "timing_unit": "project_ms", "transcript_available": bool(sw),
                    "scope": "Find primary evidence only for claims in these words; do not invent missing narration."}
        research_digest = digest(research)
        research["input_digest"] = research_digest
        research_rel = prefix + "packets/%s-%s-research.json" % (key, research_digest[:12])
        packets[research_rel] = research
        packet = {"version": VERSION, "scene_key": key, "scene": scene, "words": sw,
                  "segments": compact_segments, "segment_state_digest": digest(segs),
                  "timing_unit": "project_ms", "transcript_available": bool(sw),
                  "details": ("Full segment properties are in ../inputs/snapshot.json relative to this packet; writer re-reads live before changes."
                              if prefix else "Full segment properties are in inputs/snapshot.json; writer re-reads live before changes.")}
        packet_digest = digest(packet)
        packet["input_digest"] = packet_digest
        rel = prefix + "packets/%s-%s.json" % (key, packet_digest[:12])
        packets[rel] = packet
        text = " ".join(w[2] for w in sw) or scene.get("script", "")
        structural = b - a < 1000 / 60 or scene["name"].lower().startswith("chapter:")
        rows.append({"scene_key": key, **{k: scene[k] for k in ("id", "name", "start_ms", "end_ms")},
                     "word_count": len(sw), "segment_count": len(segs), "preview": text[:240],
                     "packet": rel, "input_digest": packet_digest, "research_packet": research_rel,
                     "research_digest": research_digest, "worker_scope": "structural-review" if structural else "narrative"})
    return rows, packets


def graph_version(config):
    version = config.get("graph_version", 1)
    require(type(version) is int and version in (1, 2), "Unsupported graph_version")
    return version


def stage_info(job, stage="baseline"):
    if graph_version(read(job / "job.json")) == 1:
        require(stage == "baseline", "Legacy jobs do not support staged ingestion")
        return {"root": "", "index": "scene-index.json"}
    return read(job / "checkpoint.json").get("stage_inputs", {}).get(stage)


def check_inputs(job, stage="baseline"):
    info = stage_info(job, stage)
    require(info is not None, "Missing " + stage + " capture; run ingest --stage " + stage)
    prefix = info["root"] + "/" if info["root"] else ""
    index = read(inside(job, info["index"]))
    snapshot = read(inside(job, prefix + "inputs/snapshot.json"))
    words = read(inside(job, prefix + "inputs/words.json"))
    require(index["input_digest"] == digest({"snapshot": snapshot, "words": words}), "Input snapshot or transcript changed")
    if info.get("input_digest"):
        require(index["input_digest"] == info["input_digest"], "Stage pointer does not match capture")
    rows, packets = packet_rows(snapshot, words, prefix)
    require(index["scenes"] == rows, "Scene index changed; re-ingest the original capture")
    require(index["timeline_hash"] == snapshot["timeline_hash"], "Index timeline hash changed")
    require(index["duration_ms"] == snapshot["duration_ms"] and index["transcript_words"] == len(words), "Index summary changed")
    for rel, packet in packets.items():
        require(read(inside(job, rel)) == packet, "Scene packet changed: " + rel)
    if stage == "baseline" and prefix:
        require(read(job / "scene-index.json") == index, "Baseline convenience index changed")
    return index


def ingest(args):
    job = job_at(args.job)
    if graph_version(read(job / "job.json")) == 1:
        require(args.stage == "baseline", "Legacy jobs do not support --stage postcut; start a v2 job")
        return ingest_v1(args)
    return ingest_v2(args)


def ingest_v1(args):
    job = job_at(args.job)
    source = Path(args.snapshot).expanduser().resolve()
    data, default_transcript = source_data(source)
    normalized = normalize(data)
    transcript = Path(args.transcript).expanduser().resolve() if args.transcript else default_transcript
    if args.transcript:
        require(transcript.exists(), "Explicit transcript path does not exist")
    words = transcript_words(transcript, normalized["timeline_hash"])
    require(all(w[1] <= normalized["duration_ms"] + 1 for w in words), "Transcript extends past project; check units and freshness")
    current = digest({"snapshot": normalized, "words": words})
    with locked(job):
        state = read(job / "checkpoint.json")
        if state["input_digest"] == current:
            try:
                check_inputs(job)
            except (Invalid, OSError, KeyError, TypeError, ValueError):
                pass  # An explicit ingest can rebuild derived files from the supplied, unchanged capture.
            else:
                return {"unchanged": True, "input_digest": current, "next": "next"}
        write(job / "inputs/snapshot.json", normalized)
        write(job / "inputs/words.json", words, compact=True)
        rows, packets = packet_rows(normalized, words)
        for rel, packet in packets.items():
            write(inside(job, rel), packet, compact=True)
        index = {"version": VERSION, "input_digest": current, "timeline_hash": normalized["timeline_hash"],
                 "project_id": normalized["project_id"] or read(job / "job.json").get("project_id"),
                 "duration_ms": normalized["duration_ms"], "transcript_words": len(words), "scenes": rows,
                 "source": str(source), "captured_at": now()}
        write(job / "scene-index.json", index)
        state["input_digest"] = current
        write(job / "checkpoint.json", state)
        result = build_tasks(job)
    return {"input_digest": current, "scenes": len(rows), "words": len(words), "tasks": result["tasks"],
            "index": str(job / "scene-index.json"), "next": "next", "visual_qa": "not performed"}


def readback_hash(job, receipt):
    """A v2 writer records an exact committed hash and independently saved readback."""
    expected = receipt.get("timeline_hash_after")
    require(isinstance(expected, str) and expected.strip(), "Writer receipt requires timeline_hash_after")
    relative = receipt.get("evidence", {}).get("readback")
    require(isinstance(relative, str) and relative in receipt.get("artifacts", []), "Writer receipt requires a readback JSON artifact")
    readback = read(inside(job, relative))
    observed = readback.get("timeline_hash", readback.get("hash"))
    require(observed == expected, "Writer timeline_hash_after differs from readback artifact")
    return expected


def bound_postcut(job, writer_task=None):
    """Return only a capture bound to the current, completed cut writer."""
    state = read(job / "checkpoint.json")
    info = state.get("stage_inputs", {}).get("postcut")
    record = state["completed"].get("write-cut")
    if not info or not record or (writer_task and record["input_digest"] != writer_task["input_digest"]):
        return None
    receipt = receipt_details(job, record)
    require(receipt["status"] == "done", "Postcut capture requires a done cut writer")
    require(info["writer_receipt"] == record["receipt"] and
            info["writer_receipt_sha256"] == file_hash(inside(job, record["receipt"])), "Postcut capture is bound to a different writer receipt")
    for relative, sha in record["files"].items():
        require(file_hash(inside(job, relative)) == sha, "Cut-writer evidence changed: " + relative)
    index = check_inputs(job, "postcut")
    require(index["timeline_hash"] == readback_hash(job, receipt), "Postcut capture does not match committed cut hash")
    return index


def ingest_v2(args):
    job = job_at(args.job)
    config = read(job / "job.json")
    source = Path(args.snapshot).expanduser().resolve()
    data, default_transcript = source_data(source)
    normalized = normalize(data)
    transcript = Path(args.transcript).expanduser().resolve() if args.transcript else default_transcript
    if args.transcript:
        require(transcript.exists(), "Explicit transcript path does not exist")
    words = transcript_words(transcript, normalized["timeline_hash"])
    require(all(w[1] <= normalized["duration_ms"] + 1 for w in words), "Transcript extends past project; check units and freshness")
    current = digest({"snapshot": normalized, "words": words})
    with locked(job):
        state = read(job / "checkpoint.json")
        info = {"input_digest": current, "root": "stages/" + args.stage + "/" + current}
        info["index"] = info["root"] + "/scene-index.json"
        if args.stage == "postcut":
            require(not config.get("plan_only") and config["mode"] != "reel", "Postcut ingestion requires executable fast/proof mode")
            ledger(job)
            record = state["completed"].get("write-cut")
            require(record is not None, "Postcut ingestion requires completed write-cut")
            receipt = receipt_details(job, record)
            require(receipt["status"] == "done", "Postcut ingestion requires a done write-cut receipt")
            expected = readback_hash(job, receipt)
            require(normalized["timeline_hash"] == expected, "Postcut timeline hash mismatch; capture the exact committed cut")
            baseline = check_inputs(job)
            if baseline.get("project_id") and normalized.get("project_id"):
                require(baseline["project_id"] == normalized["project_id"], "Postcut belongs to a different project")
            require(transcript is not None and transcript.exists() and words, "Postcut ingestion requires the freshly captured timed transcript")
            info.update(writer_receipt=record["receipt"], writer_receipt_sha256=file_hash(inside(job, record["receipt"])))
        elif state["input_digest"] != current:
            require("write-cut" not in state["completed"], "Baseline replacement after cut is blocked; use --stage postcut or explicitly reopen the cut")
        old_info = state.get("stage_inputs", {}).get(args.stage)
        if old_info == info:
            check_inputs(job, args.stage)
            return {"unchanged": True, "stage": args.stage, "input_digest": current, "next": "next"}
        prefix = info["root"] + "/"
        rows, packets = packet_rows(normalized, words, prefix)
        index = {"version": VERSION, "input_digest": current, "timeline_hash": normalized["timeline_hash"],
                 "project_id": normalized["project_id"] or config.get("project_id"), "duration_ms": normalized["duration_ms"],
                 "transcript_words": len(words), "scenes": rows, "source": str(source), "captured_at": now(), "stage": args.stage}
        index_path = inside(job, info["index"])
        if index_path.exists():
            # An identical prior capture keeps its original timestamps and bytes.
            index = read(index_path)
        else:
            write(inside(job, prefix + "inputs/snapshot.json"), normalized)
            write(inside(job, prefix + "inputs/words.json"), words, compact=True)
            for relative, packet in packets.items():
                write(inside(job, relative), packet, compact=True)
            write(index_path, index)
        state.setdefault("stage_inputs", {})[args.stage] = info
        if args.stage == "baseline":
            state["input_digest"] = current
            state["stage_inputs"].pop("postcut", None)
            write(job / "scene-index.json", index)
        write(job / "checkpoint.json", state)
        check_inputs(job, args.stage)
        result = build_tasks(job)
    return {"stage": args.stage, "input_digest": current, "scenes": len(rows), "words": len(words),
            "tasks": result["tasks"], "index": str(index_path), "next": "next", "visual_qa": "not performed"}


def task_manifest(job, config=None):
    config = config if config is not None else read(job / "job.json")
    return task_manifest_v2(job, config) if graph_version(config) == 2 else task_manifest_v1(job, config)


def task_manifest_v1(job, config=None):
    index = read(job / "scene-index.json")
    config = config if config is not None else read(job / "job.json")
    mode = config.get("mode", "proof")
    require(mode in ("fast", "proof", "reel"), "Invalid job mode")
    plan_only = config.get("plan_only", False)
    require(type(plan_only) is bool, "plan_only must be a boolean")
    scope = config.get("scene_scope", [])
    require(isinstance(scope, list), "scene_scope must be a list")
    known = {v for s in index["scenes"] for v in (s["id"], s["scene_key"])}
    require(all(s in known for s in scope), "Unknown --scene selector; use scene key or id from scene-index.json")
    tasks = []
    for s in index["scenes"]:
        if scope and s["id"] not in scope and s["scene_key"] not in scope:
            continue
        if not scope and s["worker_scope"] == "structural-review":
            continue  # Cards and sub-frame residuals remain in assemble/writer/coverage, not separate LLM jobs.
        phases = ("select-reel",) if mode == "reel" else (("research", "plan") if mode == "proof" and s["worker_scope"] == "narrative" else ("plan",))
        for phase in phases:
            tid = phase + "-" + s["scene_key"]
            light = phase in ("research", "select-reel")
            packet = s["research_packet"] if light else s["packet"]
            pd = s["research_digest"] if light else s["input_digest"]
            tasks.append({"id": tid, "role": phase, "scene_id": s["id"], "packet": packet,
                          "input_digest": digest({"phase": phase, "packet": pd, "goal": config["goal"]}),
                          "depends_on": ["research-" + s["scene_key"]] if phase == "plan" and "research" in phases else [],
                          "mutates_timeline": False, "output": "outputs/" + tid + ".json", "evidence_required": []})
    require(tasks, "No narrative scenes in scope; select structural scenes explicitly if they are the edit target")
    if mode == "reel":
        tail = (
            ("assemble-reels", "editorial-review", [t["id"] for t in tasks], []),
            ("render-reels", "local-render", ["assemble-reels"], ["export_checks"]),
            ("verify-final", "final-review", ["render-reels"], ["export_checks", "visual_review", "audio_review"]),
        )
    else:
        tail = (
            ("assemble", "editorial-review", [t["id"] for t in tasks if t["role"] == "plan"], []),
            ("write-timeline", "single-writer", ["assemble"], ["backup", "dry_run", "project_diff", "visual_review"]),
            ("verify-final", "final-review", ["write-timeline"], ["export_checks", "visual_review", "audio_review"]),
        )
    if plan_only:
        tail = tail[:1]  # An assembled plan/handoff is the final requested artifact, in every mode.
    for tid, role, dependencies, checks in tail:
        tasks.append({"id": tid, "role": role, "packet": "scene-index.json",
                      "input_digest": digest({"phase": tid, "input": index["input_digest"], "goal": config["goal"], "mode": mode, "scope": scope}),
                      "depends_on": dependencies, "mutates_timeline": tid == "write-timeline",
                      "output": "outputs/" + tid + ".json", "evidence_required": checks})
    return {"version": VERSION, "input_digest": index["input_digest"], "mode": mode, "scene_scope": scope,
            "plan_only": plan_only,
            "max_workers": config["max_workers"], "max_worker_revisions": config["policy"]["max_worker_revisions"],
            "timeline_writers": sum(t["mutates_timeline"] for t in tasks), "tasks": tasks,
            "dispatch": "Advisory manifest; harness dispatches bounded workers. Runner never executes them."}


def task_manifest_v2(job, config):
    baseline = read(job / "scene-index.json")
    mode, scope, plan_only = config["mode"], config.get("scene_scope", []), config.get("plan_only", False)
    require(mode in ("fast", "proof", "reel") and type(plan_only) is bool, "Invalid mode or plan_only")
    known = {v for s in baseline["scenes"] for v in (s["id"], s["scene_key"])}
    require(isinstance(scope, list) and all(s in known for s in scope), "Unknown --scene selector")
    scenes = [s for s in baseline["scenes"] if ((s["id"] in scope or s["scene_key"] in scope) if scope else s["worker_scope"] == "narrative")]
    require(scenes, "No scenes in scope")
    tasks, postcut = [], None

    def add(tid, tier, stage, depends, responsibility, tools, gate, evidence=(), scene=None,
            input_stage="baseline", light=False, writer=False, escalation=None):
        index = baseline if input_stage == "baseline" else postcut
        packet = (scene["research_packet"] if light else scene["packet"]) if scene else (
            stage_info(job, input_stage)["index"] if index else None)
        source = (scene["research_digest"] if light else scene["input_digest"]) if scene else (
            index["input_digest"] if index else "pending-postcut")
        task = {"id": tid, "role": tid.rsplit("-s", 1)[0] if scene else tid, "stage": stage,
                "model_tier": tier, "execution": "local" if tier == "local" else "agent",
                "owner_tier": "capable" if writer else tier,
                "responsibility": responsibility, "tools": list(tools),
                "inputs": ([packet] if packet else ["pending:postcut-index"]) + ["receipt:" + d for d in depends],
                "deliverable": "outputs/" + tid + ".json", "gate": gate,
                "input_stage": input_stage, "stage_ready": index is not None,
                "packet": packet, "input_digest": digest({"graph_version": 2, "task": tid, "source": source,
                    "goal": config["goal"], "scope": scope if scene is None else None, "mode": mode}),
                "depends_on": list(depends), "mutates_timeline": writer,
                "output": "outputs/" + tid + ".json", "evidence_required": list(evidence)}
        if scene:
            task["scene_id"] = scene["id"]
        if escalation:
            task["escalation"] = {"tier": "escalation", "when": escalation}
        tasks.append(task)
        return task

    if mode == "reel":
        for s in scenes:
            add("reel-candidates-" + s["scene_key"], "small", "reel-plan", [],
                "Propose self-contained excerpts with exact source bounds; preserve meaning and proof.",
                ["scene packet"], "Candidates are suggestions, not approved edits.", scene=s, light=True)
        add("assemble-reels", "capable", "reel-plan", [t["id"] for t in tasks],
            "Select coherent reels and approve framing/captions; record open issues honestly.",
            ["candidate receipts", "source video inspection"], "Approved reel plan or prepared plan-only handoff.",
            escalation="Ambiguous meaning, risky claims, or repeated failed planning.")
        if not plan_only:
            add("render-reels", "local", "reel-render", ["assemble-reels"],
                "Render the approved cuts from the identified master using scripts; do not reinterpret the plan.",
                ["reel.py", "ffmpeg", "ffprobe"], "Source master identity and export checks recorded.",
                ["master_identity", "export_checks"])
            add("verify-final", "capable", "final-review", ["render-reels"],
                "Review the actual exported reels continuously, including audio, proof, captions and framing.",
                ["exported files", "ffprobe", "frame/audio inspection"], "Actual-file review passes; no preview substitution.",
                ["export_checks", "visual_review", "audio_review"], escalation="Unresolved defects after one revision.")
    else:
        for s in scenes:
            add("cut-candidates-" + s["scene_key"], "small", "cut-plan", [],
                "Propose only supported cuts from exact timed words; preserve demos, qualifications and proof context.",
                ["scene packet", "upstream cut planning scripts"], "Candidate ranges and reasons; no live write.", scene=s)
            if mode == "proof":
                add("discover-proof-" + s["scene_key"], "small", "discovery", [],
                    "Find quick primary-source leads and flag critical unsupported claims; do not fully capture or render assets yet.",
                    ["source cache", "web search", "optional Firecrawl"], "Candidate URLs and uncertainty recorded, not claimed verified.", scene=s, light=True)
        add("assemble-cut", "capable", "cut-lock", [t["id"] for t in tasks],
            "Review all cut candidates and initial proof concerns, preserve meaning, and assemble the accepted cut plan. When requested, include style-reference treatment, proposed visual beats, requested versus actually used model assignments, and unresolved proof questions in the handoff; do not produce final visuals before cut lock.",
            ["candidate/discovery receipts", "kept-text tools", "targeted source playback"],
            "Editorial cut acceptance or honest prepared handoff recorded, including requested visual/model planning scope. User authorization is preserved separately; plan-only stops here.",
            escalation="Contradictory claims, unclear narrative intent, or repeated candidate failures.")
        if not plan_only:
            writer = add("write-cut", "local", "cut-write", ["assemble-cut"],
                "Capable owner executes approved cuts through the existing single-writer transaction scripts and reads back the committed project.",
                ["upstream apply_cuts.py", "snapshot.py", "transaction lock"],
                "Backup, dry run, diff, visual checks and readback pass; timeline_hash_after matches readback JSON.",
                ["backup", "dry_run", "project_diff", "visual_review", "readback"], writer=True)
            postcut = bound_postcut(job, writer)
            timing = add("postcut-timings", "local", "postcut", ["write-cut"],
                "Capture fresh committed snapshot and timed words; ingest --stage postcut bound to the cut writer's readback hash.",
                ["snapshot.py", "dump_transcript.py", "run.py ingest --stage postcut"],
                "Imported postcut hash matches the completed write-cut receipt.", ["postcut_index"])
            timing["input_digest"] = digest({"task": "postcut-timings", "baseline": baseline["input_digest"],
                "postcut": postcut["input_digest"] if postcut else None, "writer_input": writer["input_digest"]})
            add("prepare-finishing", "local", "finishing", ["postcut-timings"],
                "Prepare retained audio, caption corrections, chapter timing and existing template assets using scripts; reuse approved masters.",
                ["upstream audio/caption/chapter scripts", "ffmpeg", "ffprobe"],
                "Finishing instructions use postcut times; uncertain words remain flagged.", input_stage="postcut")
            finish_dependencies = ["prepare-finishing"]
            if mode == "proof":
                add("retained-claims", "capable", "visual-plan", ["postcut-timings"],
                    "Map surviving spoken claims to initial discovery and existing assets; discard production work for removed claims.",
                    ["postcut transcript", "discovery receipts", "source cache"],
                    "Every planned proof item is tied to a retained claim and postcut time.", input_stage="postcut")
                add("visual-spec", "capable", "visual-plan", ["retained-claims"],
                    "Choose readable proof treatment and declarative template specs; small workers may fill known templates. Use structural diagrams locally.",
                    ["existing styles", "local diagram/card templates"],
                    "One clear purpose per visual; generated media is optional and explicitly requested, never evidence.", input_stage="postcut",
                    escalation="A new visual language or unresolved semantic diagram decisions.")
                add("finalize-proof", "capable", "proof-capture", ["retained-claims"],
                    "Capture and verify only retained proof and tweets against primary sources; small assistants may capture, but this owner verifies pixels and claims.",
                    ["source cache", "browser", "optional Firecrawl"],
                    "Actual source pixels, provenance, permissions/limits and mismatch findings recorded.", ["proof_manifest"], input_stage="postcut")
                add("render-visuals", "local", "visual-render", ["visual-spec", "finalize-proof"],
                    "Render approved screenshots, crops, cards and structural diagrams with local templates; no LLM or generation call for deterministic graphics.",
                    ["upstream animation toolkit", "local templates", "ffmpeg"],
                    "Asset hashes, durations and postcut placement plan match approved specs.", ["render_manifest"], input_stage="postcut")
                add("review-visuals", "capable", "visual-review", ["render-visuals"],
                    "Inspect rendered pixels, proof accuracy, readability and timing; report precise fixes once.",
                    ["rendered frames", "proof manifest"], "Retained visuals pass pixel review before placement.",
                    ["visual_review"], input_stage="postcut", escalation="Unresolved factual or visual ambiguity after one revision.")
                finish_dependencies.append("review-visuals")
            add("write-finish", "local", "finish-write", finish_dependencies,
                "Capable owner applies approved finishing and visuals through the single timeline writer, then reads back; no independent editorial choices.",
                ["upstream placement/finishing scripts", "transaction lock", "snapshot.py"],
                "Dry run, project diff, visual checks and committed readback pass.",
                ["dry_run", "project_diff", "visual_review", "readback"], input_stage="postcut", writer=True)
            add("build-preview", "local", "preview", ["write-finish"],
                "Produce review evidence at changed joins, visual placements and audio/problem windows.",
                ["upstream preview/frame tools", "ffmpeg"], "Preview artifacts identify the committed finishing state.",
                ["preview_manifest"], input_stage="postcut")
            add("review-preview", "capable", "preview-review", ["build-preview"],
                "Review targeted changed joins, visuals, audio and known problem windows; do not repeat the default full-video review here.",
                ["preview evidence", "proof and finishing manifests"], "Known issues resolved before final export.",
                ["preview_review"], input_stage="postcut", escalation="Unresolved quality or narrative defects after one revision.")
            add("export-master", "local", "export", ["review-preview"],
                "Export the accepted whole project, check media parameters and record exact delivered-file hashes; do not publish.",
                ["upstream export/delivery scripts", "ffprobe", "ffmpeg"],
                "Full export, source timeline identity and technical checks recorded; this is not visual acceptance.",
                ["export_checks", "export_manifest"], input_stage="postcut")
            add("verify-final", "capable", "final-review", ["export-master"],
                "Inspect the actual exported file for picture, sound, captions and proof. Perform one continuous review when scope requires it; preview approval is insufficient.",
                ["actual exported file", "proof manifest", "audio/frame inspection"],
                "Actual-file review passes; optional reels start a separate reel job anchored to this master's path and hash.",
                ["export_checks", "visual_review", "audio_review"], input_stage="postcut",
                escalation="Unresolved actual-file defects after one targeted revision.")
    writer_count = sum(t["mutates_timeline"] for t in tasks)
    return {"version": VERSION, "graph_version": 2, "input_digest": baseline["input_digest"], "mode": mode,
            "scene_scope": scope, "plan_only": plan_only, "max_workers": config["max_workers"],
            "max_worker_revisions": config["policy"]["max_worker_revisions"], "timeline_writers": min(1, writer_count),
            "writer_tasks": writer_count, "tasks": tasks,
            "dispatch": "Advisory graph only. Tiers are responsibilities, not automatic provider calls; local tasks use scripts."}


def build_tasks(job):
    check_inputs(job)
    manifest = task_manifest(job)
    state = read(job / "checkpoint.json")
    old, kept = state["completed"], {}
    for t in manifest["tasks"]:
        record = old.get(t["id"])
        if record and record["input_digest"] == t["input_digest"] and all(d in kept for d in t["depends_on"]):
            receipt = receipt_details(job, record)
            if receipt["status"] == "prepared" and not manifest["plan_only"]:
                continue
            kept[t["id"]] = record
    state["completed"] = kept
    if graph_version(read(job / "job.json")) == 2 and "write-cut" not in kept:
        if state.get("stage_inputs", {}).pop("postcut", None):
            write(job / "checkpoint.json", state)
            manifest = task_manifest(job)
    write(job / "tasks.json", manifest)
    write(job / "checkpoint.json", state)
    return {"tasks": len(manifest["tasks"]), "retained_completed": len(kept), "invalidated_completed": len(old) - len(kept)}


def tasks(args):
    job = job_at(args.job)
    with locked(job):
        config = read(job / "job.json")
        if args.mode:
            config["mode"] = args.mode
        if args.scene is not None:
            config["scene_scope"] = args.scene
        elif args.all_scenes:
            config["scene_scope"] = []
        if args.plan_only is not None:
            config["plan_only"] = args.plan_only
        task_manifest(job, config)  # Validate proposed mode/scope before changing the saved job.
        write(job / "job.json", config)
        return build_tasks(job)


def ledger(job, ignore_completed=()):
    check_inputs(job)
    manifest, state = read(job / "tasks.json"), read(job / "checkpoint.json")
    require(manifest == task_manifest(job), "Task manifest is stale or edited; run tasks")
    require(manifest["input_digest"] == state["input_digest"], "Checkpoint is stale; run ingest")
    known = {t["id"]: t for t in manifest["tasks"]}
    for tid, record in state["completed"].items():
        require(tid in known, "Unknown completed task: " + tid)
        if tid in ignore_completed:
            continue  # Explicit reopen may invalidate a changed artifact; retained work is still checked.
        t = known[tid]
        require(record["input_digest"] == t["input_digest"], "Stale receipt: " + tid)
        require(all(d in state["completed"] for d in t["depends_on"]), "Completed task has incomplete dependencies: " + tid)
        for artifact, sha in record["files"].items():
            p = inside(job, artifact)
            require(p.is_file() and file_hash(p) == sha, "Receipt or artifact changed: " + artifact)
        receipt = receipt_details(job, record)
        require(manifest["plan_only"] or receipt["status"] != "prepared", "Prepared receipt cannot unlock execution: " + tid)
    return manifest, state


def receipt_details(job, record):
    relative = record["receipt"]
    path = inside(job, relative)
    require(relative in record["files"] and path.is_file() and file_hash(path) == record["files"][relative],
            "Receipt changed or missing: " + relative)
    receipt = read(path)
    require(receipt.get("status") in ("done", "prepared"), "Receipt status must be done or prepared")
    findings = receipt.get("unresolved")
    require(isinstance(findings, list) and all(isinstance(x, str) and x.strip() for x in findings),
            "Receipt unresolved must be a list of nonempty strings")
    require(receipt["status"] == "prepared" or findings == [], "Done receipt cannot contain unresolved findings")
    return receipt


def next_tasks(args):
    job = job_at(args.job)
    manifest, state = ledger(job)
    ready = [t for t in manifest["tasks"] if t["id"] not in state["completed"] and
             all(d in state["completed"] for d in t["depends_on"])]
    blockers = []
    eligible = []
    for task in ready:
        if not task.get("stage_ready", True):
            blockers.append(task["id"] + ": requires hash-bound postcut capture")
            continue
        if task["role"] in ("research", "select-reel", "cut-candidates", "discover-proof", "reel-candidates"):
            packet = read(inside(job, task["packet"]))
            if not packet["transcript_available"] and not packet["scene"].get("script"):
                blockers.append(task["id"] + ": capture timed narration or a scene script before researching claims or choosing reels")
                continue
        eligible.append(task)
    selected = eligible[:manifest["max_workers"]]
    writers = [t for t in selected if t["mutates_timeline"]]
    if writers:
        selected = writers[:1]
    if selected and selected[0]["mutates_timeline"]:
        index = read(job / "scene-index.json")
        if not index.get("timeline_hash"):
            selected = []
            blockers.append("Writer needs a fresh snapshot with timeline_hash and live preflight; re-ingest.")
    remaining = len(manifest["tasks"]) - len(state["completed"])
    unresolved = []
    prepared_count = 0
    for tid, record in state["completed"].items():
        receipt = receipt_details(job, record)
        prepared_count += receipt["status"] == "prepared"
        if receipt["unresolved"]:
            unresolved.append({"task_id": tid, "findings": receipt["unresolved"]})
    return {"ready": selected, "blocked": blockers, "completed": len(state["completed"]),
            "remaining": remaining, "plan_only": manifest["plan_only"],
            "planning_complete": manifest["plan_only"] and remaining == 0,
            "prepared_milestones": prepared_count,
            "done_milestones": len(state["completed"]) - prepared_count,
            "unresolved_handoff_findings": unresolved,
            "dispatch_policy": "Run at most this batch once; complete receipts before asking for the next batch.",
            "visual_qa": "not evaluated by runner"}


def reopen(args):
    job = job_at(args.job)
    require(args.reason.strip(), "Reopen requires a nonempty reason")
    with locked(job):
        tasks = read(job / "tasks.json")["tasks"]
        require(any(t["id"] == args.task for t in tasks), "Unknown task")
        affected = {args.task}
        for task in tasks:  # Manifest order is topological.
            if any(d in affected for d in task["depends_on"]):
                affected.add(task["id"])
        manifest, state = ledger(job, ignore_completed=affected)
        invalidated = {t["id"]: state["completed"][t["id"]] for t in manifest["tasks"]
                       if t["id"] in affected and t["id"] in state["completed"]}
        for tid in invalidated:
            del state["completed"][tid]
        state.setdefault("reopen_events", []).append({"at": now(), "task_id": args.task,
            "reason": args.reason.strip(), "input_digest": state["input_digest"],
            "invalidated_checkpoints": invalidated})
        write(job / "checkpoint.json", state)
        if graph_version(read(job / "job.json")) == 2:
            build_tasks(job)
    return {"reopened": args.task, "invalidated_checkpoints": list(invalidated),
            "pending_dependency_chain": [t["id"] for t in manifest["tasks"] if t["id"] in affected],
            "retained_checkpoints": len(state["completed"]),
            "note": "Historic receipts retained. Use new artifact paths such as outputs/plan.v2.json before completing again."}


def complete(args):
    job = job_at(args.job)
    receipt = read(Path(args.receipt).expanduser())
    with locked(job):
        manifest, state = ledger(job)
        t = next((t for t in manifest["tasks"] if t["id"] == args.task), None)
        require(t is not None, "Unknown task")
        require(t.get("stage_ready", True), "Task requires a hash-bound postcut capture")
        require(args.task not in state["completed"], "Task already completed; receipts are immutable")
        require(all(d in state["completed"] for d in t["depends_on"]), "Dependencies are incomplete")
        require(receipt.get("task_id") == args.task and receipt.get("input_digest") == t["input_digest"], "Receipt task or input digest mismatch")
        status, findings = receipt.get("status"), receipt.get("unresolved")
        require(isinstance(findings, list) and all(isinstance(x, str) and x.strip() for x in findings),
                "Receipt unresolved must be a list of nonempty strings")
        require(status in ("done", "prepared"), "Receipt status must be done or prepared")
        require(status != "prepared" or manifest["plan_only"], "Prepared receipts require a plan-only job")
        require(status == "prepared" or findings == [], "Done receipt cannot contain unresolved findings")
        require(isinstance(receipt.get("summary"), str) and receipt["summary"].strip(), "Receipt needs a summary")
        artifacts = receipt.get("artifacts")
        require(isinstance(artifacts, list) and artifacts, "Receipt needs artifacts[]")
        evidence = receipt.get("evidence", {})
        for key in t["evidence_required"]:
            require(isinstance(evidence.get(key), str) and evidence[key] in artifacts, "Missing evidence artifact: " + key)
        if t["mutates_timeline"]:
            require(read(job / "scene-index.json").get("timeline_hash"), "Cannot record writer completion without baseline timeline hash")
            if manifest.get("graph_version") == 2:
                readback_hash(job, receipt)
        if manifest.get("graph_version") == 2 and args.task == "postcut-timings":
            require(bound_postcut(job) is not None, "Capture and ingest postcut timings before completing this task")
            require(evidence.get("postcut_index") == stage_info(job, "postcut")["index"], "postcut_index evidence must point to the ingested immutable index")
        hashes = {}
        for artifact in artifacts:
            require(isinstance(artifact, str), "Artifact paths must be strings")
            p = inside(job, artifact)
            require(p.is_file(), "Artifact missing: " + artifact)
            hashes[artifact] = file_hash(p)
        receipt_rel = "receipts/" + args.task + "-" + t["input_digest"][:12] + "-" + digest(receipt)[:12] + ".json"
        write(inside(job, receipt_rel), receipt)
        hashes[receipt_rel] = file_hash(inside(job, receipt_rel))
        state["completed"][args.task] = {"input_digest": t["input_digest"], "completed_at": now(),
                                        "receipt": receipt_rel, "status": status, "files": hashes}
        write(job / "checkpoint.json", state)
    return {"recorded": args.task, "status": status, "unresolved": findings,
            "visual_qa": "worker assertion only; not verified by runner"}


def pipeline(args):
    job = job_at(args.job)
    manifest, state = ledger(job)
    nodes = []
    for task in manifest["tasks"]:
        record = state["completed"].get(task["id"])
        status = receipt_details(job, record)["status"] if record else (
            "needs-input" if not task.get("stage_ready", True) else
            "ready" if all(d in state["completed"] for d in task["depends_on"]) else "pending")
        nodes.append(dict(task, status=status))
    if args.format == "json":
        return dict(manifest, tasks=nodes, advisory=True)
    ids = {t["id"]: "n" + str(i) for i, t in enumerate(nodes)}
    lines = ["flowchart TD"]
    for task in nodes:
        label = task["id"] + " | " + task.get("model_tier", task["role"]) + " | " + task["status"]
        lines.append("  " + ids[task["id"]] + "[" + json.dumps(label) + "]")
    for task in nodes:
        for dep in task["depends_on"]:
            lines.append("  " + ids[dep] + " --> " + ids[task["id"]])
    return "\n".join(lines)


def estimate(args):
    job = job_at(args.job)
    usage, rates = read(args.usage), read(args.rates)
    require(isinstance(usage.get("entries"), list) and usage["entries"], "Usage needs nonempty entries[]")
    total, details = Decimal(0), []
    for i, entry in enumerate(usage["entries"]):
        model = entry.get("model")
        inp = count(entry.get("input_tokens", 0), "input_tokens")
        cached = count(entry.get("cached_input_tokens", 0), "cached_input_tokens")
        out = count(entry.get("output_tokens", 0), "output_tokens")
        require(cached <= inp, "cached_input_tokens must be <= total input_tokens")
        cost = Decimal(0)
        mr = rates.get("models", {}).get(model, {})
        for field, amount in (("input_per_million", inp - cached), ("cached_input_per_million", cached), ("output_per_million", out)):
            if amount:
                require(field in mr, "Missing explicit rate: %s.%s" % (model, field))
                cost += decimal(mr[field], field) * amount / 1000000
        for tool in entry.get("tools", []):
            name = tool["name"]
            units = decimal(tool["units"], "tool units")
            if units:
                tr = rates.get("tools", {}).get(name, {})
                require("per_unit" in tr, "Missing explicit tool rate: " + name)
                cost += units * decimal(tr["per_unit"], "tool rate")
        total += cost
        details.append({"entry": i, "model": model, "usd": str(cost)})
    budget = decimal(read(job / "job.json")["budget_usd"], "budget_usd")
    result = {"total_usd": str(total), "budget_usd": str(budget), "within_budget": total <= budget,
              "entries": details, "usage_digest": digest(usage), "rates_digest": digest(rates),
              "rate_as_of": rates.get("as_of"), "rate_sources": rates.get("source_urls", []),
              "scope": "Estimate for supplied usage only. Not a spend ledger, authorization, or subscription-limit estimate."}
    with locked(job):
        write(job / "estimate.json", result)
    return result


def asset(args):
    job = job_at(args.job)
    source = Path(args.file).expanduser().resolve()
    require(source.is_file(), "Asset file does not exist")
    if args.kind in ("source", "capture"):
        require(args.url, "Source/capture requires --url")
    if args.url:
        u = urlsplit(args.url)
        require(u.scheme in ("http", "https") and u.netloc and not u.username and not u.password, "Source URL must be public HTTP(S), without credentials")
    captured = args.captured_at or now()
    parse_date(captured)
    sha = file_hash(source)
    suffix = source.suffix.lower() if len(source.suffix) <= 10 else ""
    rel = "cache/objects/" + sha + suffix
    entry = {"sha256": sha, "object": rel, "bytes": source.stat().st_size, "original_name": source.name,
             "kind": args.kind, "source_url": args.url, "claim": args.claim, "captured_at": captured,
             "verification": "illustrative-not-evidence" if args.kind == "generated" else "unverified",
             "rights": args.rights or "not-recorded"}
    entry["id"] = digest(entry)[:20]
    with locked(job):
        dest = inside(job, rel)
        if dest.exists():
            require(file_hash(dest) == sha, "Cached object has been altered")
        else:
            shutil.copyfile(source, dest)
            require(file_hash(dest) == sha, "Asset changed while copying; retry")
        manifest = read(job / "assets.json")
        if not any(e["id"] == entry["id"] for e in manifest["entries"]):
            manifest["entries"].append(entry)
            write(job / "assets.json", manifest)
    return entry


def cache(args):
    job = job_at(args.job)
    max_age = decimal(args.max_age_hours, "max_age_hours")
    results = []
    for entry in read(job / "assets.json")["entries"]:
        if args.url and entry["source_url"] != args.url:
            continue
        age = (datetime.now(timezone.utc) - parse_date(entry["captured_at"])).total_seconds() / 3600
        p = inside(job, entry["object"])
        valid = p.is_file() and file_hash(p) == entry["sha256"]
        results.append({**entry, "age_hours": round(age, 3), "content_valid": valid,
                        "fresh_by_requested_age": valid and Decimal(str(age)) <= max_age})
    return {"entries": results, "note": "Age and content integrity only; cache reuse does not verify a claim or usage rights."}


def verify(args):
    job = job_at(args.job)
    errors, warnings = [], []
    try:
        config = read(job / "job.json")
        require(config.get("version") == VERSION, "Unknown job schema")
        graph_version(config)
        decimal(config["budget_usd"], "budget_usd")
        require(type(config["max_workers"]) is int and 1 <= config["max_workers"] <= 8, "Invalid worker bound")
        state = read(job / "checkpoint.json")
        if state["input_digest"] is None:
            warnings.append("No snapshot ingested; job is initialized only")
        else:
            index = check_inputs(job)
            ledger(job)
            if not index.get("timeline_hash"):
                warnings.append("No timeline hash; live writer remains blocked")
            if index["transcript_words"] == 0:
                warnings.append("No timed transcript; word-level edit planning needs capture")
        for entry in read(job / "assets.json")["entries"]:
            p = inside(job, entry["object"])
            require(p.is_file() and file_hash(p) == entry["sha256"], "Asset changed or missing: " + entry["object"])
    except (Invalid, KeyError, TypeError, OSError, ValueError) as e:
        errors.append(str(e))
    return {"structural_ok": not errors, "errors": errors, "warnings": warnings,
            "deliverable_verified": False, "visual_qa": "not performed by this runner",
            "note": "Checks local hashes, receipts and dependencies. Watch/listen to the actual export before delivery."}


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    def add(name, fn, job=True):
        s = sub.add_parser(name, help=fn.__name__)
        if job:
            s.add_argument("job")
        s.set_defaults(fn=fn)
        return s
    def dep_flags(s):
        for name in ("edit-skill", "proof-skill", "animation-kit"):
            s.add_argument("--" + name)
    dep_flags(add("doctor", doctor, False))
    s = add("init", init)
    dep_flags(s)
    s.add_argument("--goal", required=True)
    s.add_argument("--budget-usd", default="0")
    s.add_argument("--max-workers", type=int, default=2)
    s.add_argument("--project-id")
    s.add_argument("--graph-version", type=int, choices=(1, 2), default=2, help="New staged graph (2) or explicit legacy graph (1); existing jobs are never silently migrated")
    s.add_argument("--mode", choices=("fast", "proof", "reel"), default="fast")
    s.add_argument("--scene", action="append", help="Restrict tasks to a scene key/id; repeatable")
    s.add_argument("--plan-only", action="store_true", help="Stop at assembled plan/handoff; omit writer, renderer and final-review tasks")
    s = add("ingest", ingest)
    s.add_argument("--snapshot", required=True, help="snapshot.py JSON or dump_transcript.py WORK directory")
    s.add_argument("--transcript", help="Timed words JSON or directory of *words.json; project milliseconds")
    s.add_argument("--stage", choices=("baseline", "postcut"), default="baseline")
    s = add("tasks", tasks)
    s.add_argument("--mode", choices=("fast", "proof", "reel"))
    scope = s.add_mutually_exclusive_group()
    scope.add_argument("--scene", action="append", help="Replace task scope with these scene keys/ids")
    scope.add_argument("--all-scenes", action="store_true", help="Reset scope to all narrative scenes")
    execution = s.add_mutually_exclusive_group()
    execution.add_argument("--plan-only", dest="plan_only", action="store_const", const=True, default=None,
                           help="Persist stop at assembled plan/handoff")
    execution.add_argument("--execute", dest="plan_only", action="store_const", const=False,
                           help="Explicitly clear plan-only stop and include execution tasks; does not run them")
    add("next", next_tasks)
    s = add("pipeline", pipeline)
    s.add_argument("--format", choices=("mermaid", "json"), default="mermaid")
    s = add("complete", complete)
    s.add_argument("--task", required=True)
    s.add_argument("--receipt", required=True)
    s = add("reopen", reopen)
    s.add_argument("--task", required=True)
    s.add_argument("--reason", required=True)
    s = add("estimate", estimate)
    s.add_argument("--usage", required=True)
    s.add_argument("--rates", required=True)
    s = add("asset", asset)
    s.add_argument("file")
    s.add_argument("--kind", choices=("source", "capture", "generated", "template"), default="source")
    s.add_argument("--url")
    s.add_argument("--claim", default="")
    s.add_argument("--captured-at")
    s.add_argument("--rights")
    s = add("cache", cache)
    s.add_argument("--url")
    s.add_argument("--max-age-hours", default="24")
    add("verify", verify)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = args.fn(args)
        if isinstance(result, str):
            print(result)
            return 0
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 1 if result.get("structural_ok") is False or result.get("within_budget") is False else 0
    except (Invalid, OSError, KeyError, TypeError, ValueError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
