"""Offline integration tests: no Borumi, model API, network, or paid service."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "skills/video-edit-pipeline/scripts/run.py"


class RunnerTests(unittest.TestCase):
    legacy_graph = True
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.job = self.base / "job"
        self.snapshot = self.base / "snapshot.json"
        self.words = self.base / "words.json"
        self.data = {"duration": 20000, "hash": "bridge-baseline-1",
                     "scenes": [["a1", "Intro", 0, 10000], ["b2", "Demo", 10000, 20000]],
                     "layouts": {"l1": [0, 20000, "{\"kind\":\"side_by_side\"}"]},
                     "content": {"c1": ["camera_1", 0, 10000, "media-1", 0, 10000, "g1"],
                                 "c2": ["camera_1", 10000, 20000, "media-2", 0, 10000, "g2"]},
                     "overlays": {}, "controls": {}}
        self.put(self.snapshot, self.data)
        self.put(self.words, {"words": [[100, 400, "Hello"], [500, 900, "world"],
                                       [11000, 11500, "Demonstration"]]})

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def get(self, name):
        return json.loads((self.job / name).read_text())

    def cli(self, *args, code=0):
        if getattr(self, "legacy_graph", False) and args and args[0] == "init" and "--graph-version" not in args:
            args = (*args, "--graph-version", "1")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        # Isolate tests from a developer's real toolchain installation/config.
        env["VIDEO_EDIT_PIPELINE_CONFIG"] = str(self.base / "toolchain.json")
        for key in ("BORUMI_EDIT_SKILL", "PROOF_FIRST_SKILL", "BORUMI_ANIMATION_KIT"):
            env.pop(key, None)
        p = subprocess.run([sys.executable, str(RUN), *map(str, args)],
                           capture_output=True, text=True, env=env, timeout=20)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return json.loads(p.stdout or p.stderr)

    def start(self, budget="0"):
        self.cli("init", self.job, "--goal", "Keep the strongest proof; tighten the demo", "--budget-usd", budget, "--mode", "proof")
        return self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)

    def receipt(self, tid):
        task = next(t for t in self.get("tasks.json")["tasks"] if t["id"] == tid)
        artifact = "outputs/" + tid + ".json"
        self.put(self.job / artifact, {"findings": [], "note": "test output"})
        receipt = {"task_id": tid, "input_digest": task["input_digest"], "status": "done",
                   "summary": "Synthetic test receipt", "artifacts": [artifact], "unresolved": []}
        return self.put(self.base / (tid + "-receipt.json"), receipt)

    def finish(self, tid):
        return self.cli("complete", self.job, "--task", tid, "--receipt", self.receipt(tid))

    def test_init_default_budget_and_no_overwrite(self):
        result = self.cli("init", self.job, "--goal", "Make the tutorial concise")
        self.assertEqual(result["budget_usd"], "0")
        self.assertIn("Make the tutorial concise", (self.job / "goal.md").read_text())
        self.assertFalse(self.get("job.json")["policy"]["paid_calls_by_runner"])
        self.assertEqual(self.cli("init", self.job, "--goal", "Overwrite", code=2)["error"],
                         "init refuses a nonempty folder")
        result = self.cli("verify", self.job)
        self.assertTrue(result["structural_ok"])
        self.assertFalse(result["deliverable_verified"])
        self.assertTrue(result["warnings"])

    def test_reject_invalid_budget_before_creating_job(self):
        self.cli("init", self.job, "--goal", "demo", "--budget-usd", "NaN", code=2)
        self.assertFalse(self.job.exists())

    def test_ingest_compacts_and_assigns_words_by_scene(self):
        result = self.start()
        self.assertEqual((result["scenes"], result["words"], result["tasks"]), (2, 3, 7))
        index = self.get("scene-index.json")
        packet = self.get(index["scenes"][0]["packet"])
        self.assertEqual(len(packet["words"]), 2)
        self.assertTrue(all(s["start_ms"] < 10000 for s in packet["segments"]))
        self.assertLess(len(json.dumps(index)), len(json.dumps(self.get("inputs/snapshot.json"))) + 2000)
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])
        ready = self.cli("next", self.job)["ready"]
        self.assertEqual([t["id"] for t in ready], ["research-s0001", "research-s0002"])
        self.assertFalse(any(t["mutates_timeline"] for t in ready))

    def test_identical_ingest_is_noop(self):
        self.start()
        self.finish("research-s0001")
        before = self.get("checkpoint.json")
        result = self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
        self.assertTrue(result["unchanged"])
        self.assertEqual(before, self.get("checkpoint.json"))

    def test_fast_default_skips_research_and_scope_reduces_work(self):
        self.cli("init", self.job, "--goal", "Tighten scene two only")
        self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
        tasks = self.get("tasks.json")
        self.assertEqual(tasks["mode"], "fast")
        self.assertEqual(len(tasks["tasks"]), 5)
        self.assertFalse(any(t["role"] == "research" for t in tasks["tasks"]))
        self.cli("tasks", self.job, "--scene", "s0002")
        self.assertEqual(len(self.get("tasks.json")["tasks"]), 4)
        self.assertEqual(len(self.get("scene-index.json")["scenes"]), 2)
        self.assertEqual(self.cli("next", self.job)["ready"][0]["id"], "plan-s0002")
        before = self.get("job.json")
        self.cli("tasks", self.job, "--scene", "unknown", code=2)
        self.assertEqual(before, self.get("job.json"))

    def test_reel_mode_has_no_timeline_mutations(self):
        self.start()
        self.cli("tasks", self.job, "--mode", "reel", "--scene", "b2")
        tasks = self.get("tasks.json")
        self.assertEqual(tasks["timeline_writers"], 0)
        self.assertFalse(any(t["mutates_timeline"] for t in tasks["tasks"]))
        self.assertEqual([t["id"] for t in tasks["tasks"]],
                         ["select-reel-s0002", "assemble-reels", "render-reels", "verify-final"])
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_plan_only_stops_at_assembly_in_every_mode(self):
        for mode in ("fast", "proof", "reel"):
            with self.subTest(mode=mode):
                self.job = self.base / ("plan-only-" + mode)
                result = self.cli("init", self.job, "--goal", "Prepare a plan and handoff; do not apply changes yet",
                                  "--mode", mode, "--plan-only")
                self.assertTrue(result["plan_only"])
                self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
                manifest = self.get("tasks.json")
                self.assertTrue(manifest["plan_only"])
                self.assertEqual(manifest["timeline_writers"], 0)
                forbidden = {"write-timeline", "render-reels", "verify-final"}
                self.assertTrue(forbidden.isdisjoint(t["id"] for t in manifest["tasks"]))
                self.assertFalse(any(t["mutates_timeline"] for t in manifest["tasks"]))
                final_task = "assemble-reels" if mode == "reel" else "assemble"
                self.assertEqual(manifest["tasks"][-1]["id"], final_task)
                for task in manifest["tasks"]:
                    self.finish(task["id"])
                progress = self.cli("next", self.job)
                self.assertTrue(progress["planning_complete"])
                self.assertEqual(progress["remaining"], 0)
                self.assertFalse(progress["ready"])
                self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_plan_only_persists_until_explicit_execute_and_preserves_plan(self):
        self.start()
        self.cli("tasks", self.job, "--plan-only")
        for task in self.get("tasks.json")["tasks"]:
            self.finish(task["id"])
        completed = self.get("checkpoint.json")["completed"]
        self.cli("tasks", self.job)
        self.assertTrue(self.get("job.json")["plan_only"])
        self.assertTrue(self.cli("next", self.job)["planning_complete"])
        self.cli("tasks", self.job, "--execute")
        self.assertFalse(self.get("job.json")["plan_only"])
        self.assertEqual(self.get("checkpoint.json")["completed"], completed)
        next_result = self.cli("next", self.job)
        self.assertFalse(next_result["planning_complete"])
        self.assertEqual([t["id"] for t in next_result["ready"]], ["write-timeline"])

    def test_mode_change_does_not_clear_plan_only(self):
        self.start()
        self.cli("tasks", self.job, "--plan-only")
        self.cli("tasks", self.job, "--mode", "reel", "--scene", "s0002")
        self.assertTrue(self.get("job.json")["plan_only"])
        self.assertEqual([t["id"] for t in self.get("tasks.json")["tasks"]],
                         ["select-reel-s0002", "assemble-reels"])
        self.cli("tasks", self.job, "--execute")
        self.assertIn("render-reels", [t["id"] for t in self.get("tasks.json")["tasks"]])

    def test_prepared_handoff_keeps_findings_then_invalidates_before_execution(self):
        self.start()
        self.cli("tasks", self.job, "--plan-only")
        path = self.receipt("research-s0001")
        receipt = json.loads(path.read_text())
        receipt["status"] = "prepared"
        receipt["unresolved"] = ["Source screenshot pixels have not been reviewed"]
        self.put(path, receipt)
        result = self.cli("complete", self.job, "--task", "research-s0001", "--receipt", path)
        self.assertEqual(result["status"], "prepared")
        prepared_path = self.get("checkpoint.json")["completed"]["research-s0001"]["receipt"]
        for tid in ("plan-s0001", "research-s0002", "plan-s0002", "assemble"):
            self.finish(tid)
        progress = self.cli("next", self.job)
        self.assertTrue(progress["planning_complete"])
        self.assertEqual(progress["unresolved_handoff_findings"],
                         [{"task_id": "research-s0001", "findings": receipt["unresolved"]}])
        self.cli("tasks", self.job)
        self.assertEqual(self.get("checkpoint.json")["completed"]["research-s0001"]["status"], "prepared")
        self.cli("tasks", self.job, "--execute")
        remaining_done = self.get("checkpoint.json")["completed"]
        self.assertEqual(set(remaining_done), {"research-s0002", "plan-s0002"})
        progress = self.cli("next", self.job)
        self.assertEqual([t["id"] for t in progress["ready"]], ["research-s0001"])
        self.assertNotIn("write-timeline", [t["id"] for t in progress["ready"]])
        self.finish("research-s0001")
        new_path = self.get("checkpoint.json")["completed"]["research-s0001"]["receipt"]
        self.assertNotEqual(prepared_path, new_path)
        self.assertTrue((self.job / prepared_path).is_file())
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_executable_job_rejects_prepared_receipt(self):
        self.start()
        path = self.receipt("research-s0001")
        receipt = json.loads(path.read_text())
        receipt["status"] = "prepared"
        receipt["unresolved"] = ["Needs source review"]
        self.put(path, receipt)
        result = self.cli("complete", self.job, "--task", "research-s0001", "--receipt", path, code=2)
        self.assertIn("plan-only", result["error"])
        self.assertFalse(self.get("checkpoint.json")["completed"])

    def test_reopen_invalidates_dependents_preserves_independent_work_and_receipts(self):
        self.start()
        self.cli("tasks", self.job, "--plan-only")
        for task in self.get("tasks.json")["tasks"]:
            self.finish(task["id"])
        before = self.get("checkpoint.json")["completed"]
        historic_path = before["plan-s0001"]["receipt"]
        historic_bytes = (self.job / historic_path).read_bytes()
        result = self.cli("reopen", self.job, "--task", "plan-s0001", "--reason", "Creator requested a different opening")
        self.assertEqual(result["invalidated_checkpoints"], ["plan-s0001", "assemble"])
        remaining = self.get("checkpoint.json")["completed"]
        self.assertEqual(set(remaining), {"research-s0001", "research-s0002", "plan-s0002"})
        self.assertEqual((self.job / historic_path).read_bytes(), historic_bytes)
        self.assertEqual([t["id"] for t in self.cli("next", self.job)["ready"]], ["plan-s0001"])
        self.assertTrue(self.get("checkpoint.json")["reopen_events"][-1]["reason"])
        revision_artifact = "outputs/plan-s0001.v2.json"
        self.put(self.job / revision_artifact, {"opening": "revised"})
        receipt = json.loads((self.job / historic_path).read_text())
        receipt["summary"] = "Revised opening"
        receipt["artifacts"] = [revision_artifact]
        path = self.put(self.base / "revision-receipt.json", receipt)
        self.cli("complete", self.job, "--task", "plan-s0001", "--receipt", path)
        revised_path = self.get("checkpoint.json")["completed"]["plan-s0001"]["receipt"]
        self.assertNotEqual(historic_path, revised_path)
        self.assertEqual((self.job / historic_path).read_bytes(), historic_bytes)
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_reopen_can_repair_changed_target_but_not_hide_unrelated_changes(self):
        self.start()
        self.finish("research-s0001")
        self.finish("research-s0002")
        self.put(self.job / "outputs/research-s0001.json", {"changed": True})
        self.cli("reopen", self.job, "--task", "research-s0002", "--reason", "Unrelated revision", code=2)
        self.cli("reopen", self.job, "--task", "research-s0001", "--reason", "Rebuild changed artifact")
        self.assertEqual(set(self.get("checkpoint.json")["completed"]), {"research-s0002"})
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_modified_scene_invalidates_only_affected_workers_and_dependents(self):
        self.start()
        for tid in ("research-s0001", "plan-s0001", "research-s0002", "plan-s0002", "assemble"):
            self.finish(tid)
        words = json.loads(self.words.read_text())
        words["words"][0][2] = "Goodbye"
        self.put(self.words, words)
        self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
        done = self.get("checkpoint.json")["completed"]
        self.assertEqual(set(done), {"research-s0002", "plan-s0002"})
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_completion_rejects_missing_dependencies(self):
        self.start()
        result = self.cli("complete", self.job, "--task", "plan-s0001", "--receipt", self.receipt("plan-s0001"), code=2)
        self.assertIn("Dependencies", result["error"])

    def test_completion_rejects_unresolved_findings(self):
        self.start()
        path = self.receipt("research-s0001")
        value = json.loads(path.read_text())
        value["unresolved"] = ["Missing primary evidence"]
        self.put(path, value)
        self.cli("complete", self.job, "--task", "research-s0001", "--receipt", path, code=2)
        self.assertFalse(self.get("checkpoint.json")["completed"])

    def test_completion_rejects_artifacts_outside_job(self):
        self.start()
        path = self.receipt("research-s0001")
        value = json.loads(path.read_text())
        value["artifacts"] = ["../snapshot.json"]
        self.put(path, value)
        result = self.cli("complete", self.job, "--task", "research-s0001", "--receipt", path, code=2)
        self.assertIn("escapes", result["error"])

    def test_modified_output_blocks_resume(self):
        self.start()
        self.finish("research-s0001")
        self.put(self.job / "outputs/research-s0001.json", {"modified": True})
        result = self.cli("next", self.job, code=2)
        self.assertIn("changed", result["error"])
        self.assertFalse(self.cli("verify", self.job, code=1)["structural_ok"])

    def test_task_manifest_tampering_blocks_resume(self):
        self.start()
        tasks = self.get("tasks.json")
        tasks["tasks"][0]["mutates_timeline"] = True
        self.put(self.job / "tasks.json", tasks)
        self.cli("next", self.job, code=2)

    def test_scene_index_tampering_blocks_resume(self):
        self.start()
        index = self.get("scene-index.json")
        index["scenes"][0]["start_ms"] = 500
        self.put(self.job / "scene-index.json", index)
        self.cli("next", self.job, code=2)
        self.assertFalse(self.cli("verify", self.job, code=1)["structural_ok"])
        self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_structural_scenes_are_kept_for_review_without_extra_workers(self):
        self.data["scenes"][1][1] = "Chapter: Demo"
        self.put(self.snapshot, self.data)
        self.start()
        index = self.get("scene-index.json")
        self.assertEqual(len(index["scenes"]), 2)
        self.assertEqual(index["scenes"][1]["worker_scope"], "structural-review")
        tasks = self.get("tasks.json")["tasks"]
        self.assertEqual(len(tasks), 5)
        self.assertTrue(any(t["id"] == "assemble" for t in tasks))
        self.cli("tasks", self.job, "--scene", "s0002")
        self.assertEqual(self.cli("next", self.job)["ready"][0]["id"], "plan-s0002")

    def test_research_packets_omit_layouts_and_block_missing_narration(self):
        self.cli("init", self.job, "--goal", "edit", "--mode", "proof")
        self.cli("ingest", self.job, "--snapshot", self.snapshot)
        result = self.cli("next", self.job)
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["blocked"]), 2)
        index = self.get("scene-index.json")
        research = self.get(index["scenes"][0]["research_packet"])
        self.assertNotIn("segments", research)

    def test_writer_requires_evidence_files(self):
        self.start()
        for tid in ("research-s0001", "plan-s0001", "research-s0002", "plan-s0002", "assemble"):
            self.finish(tid)
        ready = self.cli("next", self.job)["ready"]
        self.assertEqual([t["id"] for t in ready], ["write-timeline"])
        result = self.cli("complete", self.job, "--task", "write-timeline", "--receipt", self.receipt("write-timeline"), code=2)
        self.assertIn("Missing evidence", result["error"])

    def test_costs_use_exact_supplied_cached_output_and_tool_rates(self):
        self.start("1")
        usage = self.put(self.base / "usage.json", {"entries": [{"model": "example", "input_tokens": 1000,
            "cached_input_tokens": 250, "output_tokens": 100, "tools": [{"name": "search", "units": 2}]}]})
        rates = self.put(self.base / "rates.json", {"models": {"example": {"input_per_million": "2",
            "cached_input_per_million": "0.2", "output_per_million": "10"}}, "tools": {"search": {"per_unit": "0.01"}}})
        result = self.cli("estimate", self.job, "--usage", usage, "--rates", rates)
        self.assertEqual(result["total_usd"], "0.02255")
        self.assertTrue(result["within_budget"])

    def test_paid_estimate_exceeds_default_zero_budget(self):
        self.start()
        usage = self.put(self.base / "usage.json", {"entries": [{"model": "example", "output_tokens": 1}]})
        rates = self.put(self.base / "rates.json", {"models": {"example": {"output_per_million": "1"}}})
        result = self.cli("estimate", self.job, "--usage", usage, "--rates", rates, code=1)
        self.assertFalse(result["within_budget"])

    def test_unknown_rate_and_bad_cache_accounting_fail_closed(self):
        self.start()
        usage = self.put(self.base / "usage.json", {"entries": [{"model": "example", "input_tokens": 1}]})
        rates = self.put(self.base / "rates.json", {"models": {}})
        self.cli("estimate", self.job, "--usage", usage, "--rates", rates, code=2)
        self.put(usage, {"entries": [{"model": "example", "cached_input_tokens": 1}]})
        self.cli("estimate", self.job, "--usage", usage, "--rates", rates, code=2)

    def test_asset_cache_tracks_age_integrity_and_generated_status(self):
        self.start()
        f = self.base / "proof.txt"
        f.write_text("Captured primary-source text", encoding="utf-8")
        item = self.cli("asset", self.job, f, "--url", "https://example.com/proof", "--claim", "A claim",
                        "--captured-at", "2000-01-01T00:00:00Z")
        self.assertEqual(item["verification"], "unverified")
        cached = self.cli("cache", self.job, "--url", "https://example.com/proof")["entries"]
        self.assertTrue(cached[0]["content_valid"])
        self.assertFalse(cached[0]["fresh_by_requested_age"])
        generated = self.cli("asset", self.job, f, "--kind", "generated")
        self.assertEqual(generated["verification"], "illustrative-not-evidence")
        self.assertEqual(item["object"], generated["object"])
        (self.job / item["object"]).write_text("tampered", encoding="utf-8")
        self.assertFalse(self.cli("verify", self.job, code=1)["structural_ok"])

    def test_export_directory_and_borumi_transcript_shape(self):
        export = self.base / "export"
        self.put(export / "scenes.json", {"scenes": [{"id": "s1", "display_name": "Opening", "position": 1,
            "start_ms": 0, "end_ms": 1000}]})
        self.put(export / "timeline_summary.json", {"project_id": "p1", "duration_ms": 1000,
            "timeline_hash": "h1", "layers": []})
        self.put(export / "transcript/scene01_s1_words.json", {"timeline_hash": "h1", "layers": [{"id": "mic",
            "segments": [{"items": [[100, 200, "hello"], [250, 300, "there"]]}]}]})
        self.cli("init", self.job, "--goal", "Tighten this")
        result = self.cli("ingest", self.job, "--snapshot", export)
        self.assertEqual(result["words"], 2)
        self.assertEqual(self.get("scene-index.json")["project_id"], "p1")
        self.put(export / "mic_segments.json", {"timeline_hash": "stale", "layers": []})
        self.cli("ingest", self.job, "--snapshot", export, code=2)

    def test_bad_scene_and_second_based_transcripts_are_rejected(self):
        self.cli("init", self.job, "--goal", "edit")
        self.data["scenes"][1][0] = "a1"
        self.put(self.snapshot, self.data)
        self.cli("ingest", self.job, "--snapshot", self.snapshot, code=2)
        self.data["scenes"][1][0] = "b2"
        self.put(self.snapshot, self.data)
        self.put(self.words, {"words": [{"start": 1.2, "end": 1.3, "word": "hello"}]})
        self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words, code=2)

    def test_existing_job_lock_prevents_mutation(self):
        self.start()
        (self.job / ".run.lock").mkdir()
        self.cli("tasks", self.job, code=2)

    def test_doctor_finds_configured_original_repo(self):
        edit = self.base / "edit"
        self.put(edit / "scripts/applylib.py", {})
        repo = self.base / "proof"
        self.put(repo / "plugins/proof-first-video-editor/skills/proof-first-video-editor/scripts/borumi/snapshot.py", {})
        self.put(self.base / "toolchain.json", {"paths": {"edit": str(edit), "proof": str(repo)}})
        result = self.cli("doctor")
        self.assertTrue(result["dependencies"]["edit_skill"]["present"])
        self.assertTrue(result["dependencies"]["proof_skill"]["present"])
        self.assertFalse(result["live_bridge_checked"])


class PipelineTests(unittest.TestCase):
    setUp = RunnerTests.setUp
    tearDown = RunnerTests.tearDown
    put = RunnerTests.put
    get = RunnerTests.get
    cli = RunnerTests.cli

    def start_v2(self, mode="proof", plan_only=False):
        args = ["init", self.job, "--goal", "Improve the edit without changing meaning", "--mode", mode]
        if plan_only:
            args.append("--plan-only")
        self.cli(*args)
        return self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)

    def make_receipt(self, tid, status="done", after_hash=None):
        task = next(t for t in self.get("tasks.json")["tasks"] if t["id"] == tid)
        suffix = ".r" + str(len(self.get("checkpoint.json").get("reopen_events", [])))
        artifact = "outputs/" + tid + suffix + ".json"
        self.put(self.job / artifact, {"synthetic": True, "task": tid})
        receipt = {"task_id": tid, "input_digest": task["input_digest"], "status": status,
                   "summary": "Synthetic test evidence, not actual video QA", "artifacts": [artifact],
                   "unresolved": ["Requires source pixel review"] if status == "prepared" else [], "evidence": {}}
        for key in task["evidence_required"]:
            if key == "postcut_index":
                path = self.get("checkpoint.json")["stage_inputs"]["postcut"]["index"]
            else:
                path = "outputs/" + tid + suffix + "." + key + ".json"
                value = {"synthetic": True, "check": key}
                if key == "readback":
                    receipt["timeline_hash_after"] = after_hash or ("cut-committed-2" if tid == "write-cut" else "finish-committed-3")
                    value = {"timeline_hash": receipt["timeline_hash_after"]}
                self.put(self.job / path, value)
            receipt["evidence"][key] = path
            receipt["artifacts"].append(path)
        return self.put(self.base / (tid + suffix + "-receipt.json"), receipt)

    def finish_v2(self, tid, status="done", after_hash=None):
        return self.cli("complete", self.job, "--task", tid, "--receipt", self.make_receipt(tid, status, after_hash))

    def finish_cut(self, after_hash="cut-committed-2"):
        for task in self.get("tasks.json")["tasks"]:
            if task["id"] not in self.get("checkpoint.json")["completed"]:
                self.finish_v2(task["id"], after_hash=after_hash if task["id"] == "write-cut" else None)
            if task["id"] == "write-cut":
                break

    def postcut_files(self, timeline_hash="cut-committed-2"):
        snapshot = json.loads(json.dumps(self.data))
        snapshot.update(duration=18000, hash=timeline_hash)
        snapshot["scenes"] = [["a1", "Intro", 0, 9000], ["b2", "Demo", 9000, 18000]]
        snapshot["layouts"]["l1"][1] = 18000
        snapshot["content"]["c1"] = ["camera_1", 0, 9000, "media-1", 0, 9000, "g1"]
        snapshot["content"]["c2"] = ["camera_1", 9000, 18000, "media-2", 0, 9000, "g2"]
        snap = self.put(self.base / "postcut.json", snapshot)
        words = self.put(self.base / "postcut-words.json", {"timeline_hash": timeline_hash,
            "words": [[100, 400, "Hello"], [500, 900, "world"], [10000, 10500, "Demonstration"]]})
        return snap, words

    def ingest_postcut(self, timeline_hash="cut-committed-2"):
        snap, words = self.postcut_files(timeline_hash)
        return self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", snap, "--transcript", words)

    def test_default_v2_graph_roles_parallel_discovery_and_real_export_review(self):
        self.start_v2()
        manifest = self.get("tasks.json")
        tasks = {t["id"]: t for t in manifest["tasks"]}
        self.assertEqual(self.get("job.json")["graph_version"], 2)
        self.assertEqual(manifest["timeline_writers"], 1)
        self.assertEqual(manifest["writer_tasks"], 2)
        self.assertEqual([t["id"] for t in self.cli("next", self.job)["ready"]],
                         ["cut-candidates-s0001", "discover-proof-s0001"])
        self.assertEqual(tasks["cut-candidates-s0001"]["model_tier"], "small")
        self.assertEqual(tasks["assemble-cut"]["model_tier"], "capable")
        self.assertEqual(len(tasks["assemble-cut"]["depends_on"]), 4)
        self.assertEqual(tasks["finalize-proof"]["model_tier"], "capable")
        self.assertEqual(tasks["render-visuals"]["model_tier"], "local")
        self.assertEqual(tasks["write-cut"]["owner_tier"], "capable")
        self.assertEqual(tasks["verify-final"]["depends_on"], ["export-master"])
        self.assertEqual(tasks["prepare-finishing"]["depends_on"], ["postcut-timings"])
        self.assertEqual(tasks["retained-claims"]["depends_on"], ["postcut-timings"])
        for task in tasks.values():
            for field in ("responsibility", "model_tier", "tools", "inputs", "deliverable", "gate"):
                self.assertTrue(task[field])
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_staged_ingest_preserves_cut_and_runs_through_actual_file_review(self):
        self.start_v2()
        self.finish_cut()
        before = self.get("checkpoint.json")["completed"]
        baseline = self.get("scene-index.json")
        snap, words = self.postcut_files()
        self.cli("ingest", self.job, "--snapshot", snap, "--transcript", words, code=2)
        self.assertEqual(self.get("scene-index.json"), baseline)
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", snap, "--transcript", words)
        self.assertEqual(self.get("checkpoint.json")["completed"], before)
        self.assertEqual(self.get("scene-index.json"), baseline)
        self.finish_v2("postcut-timings")
        self.assertEqual([t["id"] for t in self.cli("next", self.job)["ready"]], ["prepare-finishing", "retained-claims"])
        for task in self.get("tasks.json")["tasks"]:
            if task["id"] not in self.get("checkpoint.json")["completed"]:
                self.finish_v2(task["id"])
        self.assertEqual(self.cli("next", self.job)["remaining"], 0)
        result = self.cli("verify", self.job)
        self.assertTrue(result["structural_ok"])
        self.assertFalse(result["deliverable_verified"])

    def test_postcut_requires_writer_and_rejects_stale_snapshot_or_words(self):
        self.start_v2()
        snap, words = self.postcut_files()
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", snap, "--transcript", words, code=2)
        self.finish_cut()
        wrong_snap, wrong_words = self.postcut_files("wrong-hash")
        result = self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", wrong_snap, "--transcript", wrong_words, code=2)
        self.assertIn("hash mismatch", result["error"])
        snap, words = self.postcut_files()
        value = json.loads(words.read_text())
        value["timeline_hash"] = "bridge-baseline-1"
        self.put(words, value)
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", snap, "--transcript", words, code=2)
        self.assertNotIn("postcut", self.get("checkpoint.json")["stage_inputs"])

    def test_writer_readback_hash_is_checked_and_bound_to_receipt(self):
        self.start_v2("fast")
        for task in self.get("tasks.json")["tasks"]:
            if task["id"] == "write-cut":
                break
            self.finish_v2(task["id"])
        path = self.make_receipt("write-cut")
        receipt = json.loads(path.read_text())
        receipt["timeline_hash_after"] = "does-not-match"
        self.put(path, receipt)
        self.cli("complete", self.job, "--task", "write-cut", "--receipt", path, code=2)
        self.finish_v2("write-cut")
        record = self.get("checkpoint.json")["completed"]["write-cut"]
        committed = json.loads((self.job / record["receipt"]).read_text())
        self.put(self.job / committed["evidence"]["readback"], {"timeline_hash": "tampered"})
        snap, words = self.postcut_files()
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", snap, "--transcript", words, code=2)

    def test_reopen_cut_clears_active_postcut_and_revised_cut_can_be_ingested(self):
        self.start_v2("fast")
        self.finish_cut()
        self.ingest_postcut()
        self.finish_v2("postcut-timings")
        old_info = self.get("checkpoint.json")["stage_inputs"]["postcut"]
        self.cli("reopen", self.job, "--task", "write-cut", "--reason", "Revise one cut")
        self.assertNotIn("postcut", self.get("checkpoint.json")["stage_inputs"])
        self.assertTrue((self.job / old_info["index"]).exists())
        self.finish_v2("write-cut", after_hash="revised-cut-4")
        self.ingest_postcut("revised-cut-4")
        self.finish_v2("postcut-timings")
        self.assertTrue(self.cli("verify", self.job)["structural_ok"])

    def test_postcut_transcript_refresh_invalidates_timing_not_cut(self):
        self.start_v2()
        self.finish_cut()
        self.ingest_postcut()
        self.finish_v2("postcut-timings")
        self.finish_v2("retained-claims")
        cut_record = self.get("checkpoint.json")["completed"]["write-cut"]
        words = self.base / "postcut-words.json"
        value = json.loads(words.read_text())
        value["words"][0][2] = "Corrected"
        self.put(words, value)
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", self.base / "postcut.json", "--transcript", words)
        completed = self.get("checkpoint.json")["completed"]
        self.assertEqual(completed["write-cut"], cut_record)
        self.assertNotIn("postcut-timings", completed)
        self.assertNotIn("retained-claims", completed)

    def test_v2_plan_only_prepared_all_modes_and_legacy_versionless(self):
        for mode in ("fast", "proof", "reel"):
            with self.subTest(mode=mode):
                self.job = self.base / ("v2-plan-" + mode)
                self.start_v2(mode, plan_only=True)
                manifest = self.get("tasks.json")
                self.assertEqual(manifest["timeline_writers"], 0)
                final = "assemble-reels" if mode == "reel" else "assemble-cut"
                self.assertEqual(manifest["tasks"][-1]["id"], final)
                for task in manifest["tasks"]:
                    self.finish_v2(task["id"], status="prepared" if task["id"] == final else "done")
                self.assertTrue(self.cli("next", self.job)["planning_complete"])
                self.cli("tasks", self.job, "--execute")
                self.assertNotIn(final, self.get("checkpoint.json")["completed"])
        self.job = self.base / "legacy"
        self.cli("init", self.job, "--goal", "Old job", "--graph-version", "1")
        config = self.get("job.json")
        config.pop("graph_version")
        self.put(self.job / "job.json", config)
        self.cli("ingest", self.job, "--snapshot", self.snapshot, "--transcript", self.words)
        self.assertIn("assemble", [t["id"] for t in self.get("tasks.json")["tasks"]])
        self.assertNotIn("assemble-cut", [t["id"] for t in self.get("tasks.json")["tasks"]])
        self.cli("ingest", self.job, "--stage", "postcut", "--snapshot", self.snapshot, "--transcript", self.words, code=2)

    def test_pipeline_json_and_raw_mermaid_show_real_dependencies(self):
        self.start_v2()
        result = self.cli("pipeline", self.job, "--format", "json")
        self.assertEqual(result["graph_version"], 2)
        self.assertEqual(result["tasks"][0]["status"], "ready")
        p = subprocess.run([sys.executable, str(RUN), "pipeline", str(self.job), "--format", "mermaid"],
                           capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.startswith("flowchart TD\n"))
        self.assertIn("cut-candidates-s0001 | small | ready", p.stdout)
        self.assertIn(" --> ", p.stdout)


if __name__ == "__main__":
    unittest.main()
