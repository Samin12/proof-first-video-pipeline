#!/usr/bin/env python3
"""Install the portable skill and fetch an isolated, pinned Borumi toolchain.

Does not edit provider configuration, start services, or touch video projects.
Run --help for explicit setup, paths, and tool execution commands.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
PINS = {
    "proof": ("https://github.com/Samin12/proof-first-video-editor.git", "916cce389481c68b7ec4f292d3f8247e34a9b0ae", "plugins/proof-first-video-editor/skills/proof-first-video-editor"),
    "edit": ("https://github.com/Samin12/edit-borumi-video.git", "48a9b0439504cc42a091977fa3af28ddd55bad00", "plugins/edit-borumi-video/skills/edit-borumi-video"),
    "animation": ("https://github.com/Samin12/opencutagent-borumi.git", "efbc26cf57445fa17981faca3e38f3cb5f4e3847", ""),
}


def call(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def install(harness, home):
    # Both Codex and Grok document shared Agent Skills discovery here.
    targets = {"shared": ".agents/skills", "codex": ".agents/skills",
               "grok": ".grok/skills", "claude": ".claude/skills"}
    dest = home / targets[harness] / "video-edit-pipeline"
    if dest.is_symlink() and dest.resolve() == SKILL:
        return {"installed": str(dest), "status": "already linked"}
    if dest.exists() or dest.is_symlink():
        raise ValueError(f"Refusing to replace existing skill: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(SKILL, target_is_directory=True)
    return {"installed": str(dest), "source": str(SKILL), "status": "linked"}


def patch_bridge(edit_skill):
    """Pinned upstream auto-accepts MCP elicitation. Our isolated copy declines."""
    path = edit_skill / "scripts/bridge/bmcpd.py"
    original = path.read_text()
    old = '"result": {"action": "accept", "content": {}}'
    new = '"result": {"action": "decline"}'
    if original.count(old) == 1:
        updated = original.replace(old, new).replace(
            "elicitation/create is auto-accepted (there is no human here).",
            "elicitation/create is declined; the user must handle consent in the app.")
        path.write_text(updated)
    elif new not in original or old in original:
        raise ValueError("Bridge patch no longer matches; review the pinned dependency before use")


def fetch(home):
    base = home / ".video-edit-pipeline"
    base.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "bridge_port": 47813, "pins": {}}
    for name, (url, commit, subdir) in PINS.items():
        dest = base / "vendor" / name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            call(["git", "clone", "--quiet", "--no-checkout", url, dest])
            call(["git", "-C", dest, "checkout", "--quiet", "--detach", commit])
        else:
            head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
            if head != commit:
                raise ValueError(f"Refusing to reset existing checkout {dest}: {head} != {commit}")
        skill = dest / subdir
        if name == "edit":
            patch_bridge(skill)
        result[name] = str(skill)
        result["pins"][name] = commit
    result["animation_kit"] = str(home / ".borumi-agent/animation-kit")
    result["bridge_policy"] = "decline MCP elicitation; isolated port 47813"
    config = base / "toolchain.json"
    temp = config.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2) + "\n")
    temp.replace(config)
    return result


def load(home):
    file = home / ".video-edit-pipeline/toolchain.json"
    if not file.is_file():
        raise ValueError(f"Toolchain missing. Run setup.py --home '{home}' fetch first.")
    return json.loads(file.read_text())


def run_tool(home, component, script, rest):
    config = load(home)
    root = (Path(config[component]) / "scripts").resolve()
    file = (root / script).resolve()
    if root not in file.parents or not file.is_file():
        raise ValueError("Tool must be an existing file inside the component's scripts directory")
    env = os.environ.copy()
    env.update(BORUMI_EDIT_SKILL=config["edit"], PROOF_FIRST_SKILL=config["proof"],
               BORUMI_MCP_DIR=str(Path(config["animation"]) / "scripts"),
               BORUMI_BRIDGE_PORT=str(config["bridge_port"]))
    if file.suffix == ".sh":
        executable = "bash"
    elif file.suffix in (".mjs", ".js"):
        executable = "node"
    else:
        executable = sys.executable
    return subprocess.run([executable, str(file), *rest], env=env).returncode


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home", type=Path, default=Path.home(), help="Override user home for isolated installation tests")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("install", help="Link just this skill; no downloads or configuration changes")
    i.add_argument("--harness", choices=["shared", "codex", "grok", "claude"], default="shared")
    sub.add_parser("fetch", help="Fetch pinned public dependencies into a new isolated toolchain")
    sub.add_parser("paths", help="Print private local paths and pinned dependency versions")
    r = sub.add_parser("run", help="Execute an existing dependency script with the correct environment")
    r.add_argument("component", choices=list(PINS))
    r.add_argument("script", help="Relative path inside component/scripts, e.g. borumi/snapshot.py")
    r.add_argument("args", nargs=argparse.REMAINDER)
    a = p.parse_args(argv)
    try:
        if a.command == "install":
            out = install(a.harness, a.home.expanduser())
        elif a.command == "fetch":
            out = fetch(a.home.expanduser())
        elif a.command == "paths":
            out = load(a.home.expanduser())
        else:
            return run_tool(a.home.expanduser(), a.component, a.script, a.args)
        print(json.dumps(out, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        print(f"setup: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
