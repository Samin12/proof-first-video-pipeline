import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "skills/video-edit-pipeline/scripts" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


setup, reel = module("setup"), module("reel")


class MediaTests(unittest.TestCase):
    def info(self):
        return {"streams": [{"codec_type": "video", "width": 1920, "height": 1080}, {"codec_type": "audio"}],
                "format": {"duration": "10.0"}}

    def test_frame_mapping_and_safe_command(self):
        fps, size, rows = reel.plan_ranges({"clips": [{"in": 1.01, "out": 2.02}, {"in": 5, "out": 7}]}, self.info())
        self.assertEqual(rows[-1]["output_end_frame"], 91)
        cmd = reel.command(Path("a file $(echo secret).mp4"), Path("output.mp4"), self.info(), fps, size, rows)
        self.assertIn("a file $(echo secret).mp4", cmd)
        self.assertNotIn("shell", cmd)

    def test_bad_ranges_rejected(self):
        for row in ({"in": 3, "out": 2}, {"in": 0, "out": 11}, {"in": float("nan"), "out": 2},
                    {"in": 0, "out": 1, "crop": [0, 0, 2000, 1080]}):
            with self.assertRaises(ValueError):
                reel.plan_ranges({"clips": [row]}, self.info())

    def test_srt_reorders_and_clips(self):
        _, _, rows = reel.plan_ranges({"clips": [{"in": 5, "out": 7}, {"in": 1, "out": 2}]}, self.info())
        srt = "1\n00:00:00,900 --> 00:00:01,500\nFirst\n\n2\n00:00:05,200 --> 00:00:05,900\nSecond\n"
        mapped, clipped = reel.map_srt(srt, rows, 30)
        self.assertLess(mapped.index("Second"), mapped.index("First"))
        self.assertIn("00:00:02,000 --> 00:00:02,500", mapped)
        self.assertEqual(clipped, 1)

    def test_empty_srt_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            reel.map_srt("broken caption", [], 30)


class SetupTests(unittest.TestCase):
    def test_install_is_repeatable_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            first = setup.install("shared", home)
            self.assertTrue(Path(first["installed"]).is_symlink())
            self.assertEqual(setup.install("shared", home)["status"], "already linked")
            conflict = home / ".grok/skills/video-edit-pipeline"
            conflict.mkdir(parents=True)
            (conflict / "keep.txt").write_text("user data")
            with self.assertRaises(ValueError):
                setup.install("grok", home)
            self.assertEqual((conflict / "keep.txt").read_text(), "user data")

    def test_legacy_automatic_consent_is_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "scripts/bridge/bmcpd.py"
            path.parent.mkdir(parents=True)
            path.write_text('resp = {"result": {"action": "accept", "content": {}}}\n')
            setup.patch_bridge(root)
            setup.patch_bridge(root)
            self.assertIn('"action": "decline"', path.read_text())
            self.assertNotIn('"action": "accept"', path.read_text())


if __name__ == "__main__":
    unittest.main()
