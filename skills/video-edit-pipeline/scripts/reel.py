#!/usr/bin/env python3
"""Render a local reel from a reviewed master and explicit ranges; never edits Borumi.

Plan JSON: {"source":"/path/master.mp4", "fps":30, "size":[1080,1920],
 "clips":[{"in":12.0,"out":32.0,"crop":[0,0,1920,1080]}], "srt":"optional.srt"}
crop is optional and uses source pixels. Default is contain/pad, preserving proof.
This creates a review draft; caption accuracy and phone readability need visual QA.
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import uuid


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ], text=True))


def frame(value, fps):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        raise ValueError("Clip times must be finite and nonnegative")
    return int((value * fps).to_integral_value(rounding=ROUND_HALF_UP))


def plan_ranges(plan, info):
    fps = plan.get("fps", 30)
    if not isinstance(fps, int) or isinstance(fps, bool) or fps not in (24, 25, 30, 50, 60):
        raise ValueError("fps must be 24, 25, 30, 50, or 60")
    size = plan.get("size", [1080, 1920])
    if len(size) != 2 or any(type(v) is not int or v < 16 or v > 7680 or v % 2 for v in size):
        raise ValueError("size must contain two positive even pixel dimensions <=7680")
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("Source has no video stream")
    duration = float(info["format"]["duration"])
    if not math.isfinite(duration):
        raise ValueError("Unknown source duration")
    clips = plan.get("clips", [])
    if not 1 <= len(clips) <= 30:
        raise ValueError("Supply 1–30 explicit clips per reel")
    mapped, cursor = [], 0
    for clip in clips:
        a, b = frame(clip["in"], fps), frame(clip["out"], fps)
        if b <= a or b / fps > duration + 0.5 / fps:
            raise ValueError("Clip is empty, reversed, or beyond the source duration")
        crop = clip.get("crop")
        if crop is not None:
            if (len(crop) != 4 or any(type(x) is not int or x < 0 for x in crop)
                    or crop[2] < 2 or crop[3] < 2
                    or crop[0] + crop[2] > video["width"]
                    or crop[1] + crop[3] > video["height"]):
                raise ValueError("crop must be a valid [x,y,width,height] within source pixels")
        mapped.append({"source_start_frame": a, "source_end_frame": b,
                       "output_start_frame": cursor, "output_end_frame": cursor + b - a,
                       "crop": crop})
        cursor += b - a
    return fps, size, mapped


def command(source, target, info, fps, size, mapped):
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-n"]
    audio = any(s["codec_type"] == "audio" for s in info["streams"])
    filters, concat = [], []
    for i, clip in enumerate(mapped):
        start = clip["source_start_frame"] / fps
        length = (clip["source_end_frame"] - clip["source_start_frame"]) / fps
        cmd += ["-ss", f"{start:.9f}", "-t", f"{length:.9f}", "-i", str(source)]
        chain = f"[{i}:v:0]setpts=PTS-STARTPTS,"
        if clip["crop"]:
            x, y, w, h = clip["crop"]
            chain += f"crop={w}:{h}:{x}:{y},"
        w, h = size
        chain += (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                  f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x111111,setsar=1,"
                  f"fps={fps},trim=duration={length:.9f},setpts=PTS-STARTPTS[v{i}]")
        filters.append(chain)
        concat.append(f"[v{i}]")
        if audio:
            filters.append(f"[{i}:a:0]aresample=48000,apad,atrim=duration={length:.9f},asetpts=PTS-STARTPTS[a{i}]")
            concat.append(f"[a{i}]")
    filters.append("".join(concat) + f"concat=n={len(mapped)}:v=1:a={int(audio)}[v]" + ("[a]" if audio else ""))
    cmd += ["-filter_complex", ";".join(filters), "-map", "[v]"]
    if audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{mapped[-1]['output_end_frame']/fps:.9f}", str(target)]
    return cmd


def millis(value):
    h, m, rest = value.split(":")
    s, ms = rest.replace(".", ",").split(",")
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def stamp(ms):
    ms = round(ms)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def map_srt(text, mapped, fps):
    pattern = re.compile(r"(\d+:\d{2}:\d{2}[,.]\d{3})\s+-->\s+(\d+:\d{2}:\d{2}[,.]\d{3})[^\n]*\n([\s\S]*?)(?=\n\s*\n|\Z)")
    cues = [(millis(a), millis(b), t.strip()) for a, b, t in pattern.findall(text.replace("\r\n", "\n"))]
    if text.strip() and not cues:
        raise ValueError("Could not parse supplied SRT captions")
    out, clipped = [], 0
    for clip in mapped:
        start, end = clip["source_start_frame"] * 1000 / fps, clip["source_end_frame"] * 1000 / fps
        offset = clip["output_start_frame"] * 1000 / fps - start
        for a, b, t in cues:
            lo, hi = max(a, start), min(b, end)
            if hi > lo:
                clipped += int(lo != a or hi != b)
                out.append(f"{len(out)+1}\n{stamp(lo+offset)} --> {stamp(hi+offset)}\n{t}\n")
    return "\n".join(out), clipped


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--plan-only", action="store_true", help="Probe, validate, and print mapping without rendering")
    a = p.parse_args(argv)
    temp = None
    try:
        plan = json.loads(a.plan.read_text())
        source = (a.plan.parent / Path(plan["source"]).expanduser()).resolve()
        output = a.output.expanduser().resolve()
        if output.suffix.lower() != ".mp4":
            raise ValueError("Output must end in .mp4")
        receipt = output.with_suffix(".receipt.json")
        srt = output.with_suffix(".srt")
        for f in (output, receipt, srt):
            if f.exists():
                raise ValueError(f"Refusing to overwrite {f}")
        info = probe(source)
        fps, size, mapped = plan_ranges(plan, info)
        report = {"state": "planned", "fps": fps, "size": size, "clips": mapped,
                  "duration_seconds": mapped[-1]["output_end_frame"] / fps,
                  "visual_qa": "pending", "audio_qa": "pending", "caption_qa": "pending"}
        captions, clipped = None, 0
        if plan.get("srt"):
            captions, clipped = map_srt((a.plan.parent / Path(plan["srt"]).expanduser()).read_text(), mapped, fps)
        report["partially_clipped_caption_cues"] = clipped
        if a.plan_only:
            print(json.dumps(report, indent=2))
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(f".{output.stem}.{uuid.uuid4().hex}.partial.mp4")
        subprocess.run(command(source, temp, info, fps, size, mapped), check=True)
        rendered = probe(temp)
        stream = next(s for s in rendered["streams"] if s["codec_type"] == "video")
        actual = float(rendered["format"]["duration"])
        if [stream["width"], stream["height"]] != size or abs(actual-report["duration_seconds"]) > max(0.15, 2/fps):
            raise ValueError("Rendered dimensions or duration did not match the plan")
        # Exclusive hardlink publishes atomically without replacing an existing output.
        import os
        os.link(temp, output)
        temp.unlink()
        temp = None
        if captions is not None:
            with srt.open("x") as f:
                f.write(captions)
        report.update(state="rendered_review_draft", source=str(source), output=str(output),
                      source_sha256=digest(source), output_sha256=digest(output),
                      actual_duration_seconds=actual)
        with receipt.open("x") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, ArithmeticError, StopIteration, subprocess.CalledProcessError) as e:
        print(f"reel: {e}", file=sys.stderr)
        return 2
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
