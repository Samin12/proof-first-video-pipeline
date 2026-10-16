# Setup and harnesses

## Install once

Requires Python 3.9+. The local job helpers use the standard library. FFmpeg/ffprobe are required for media operations. Actual timeline editing runs on the Mac with Borumi and its MCP capability enabled. Browser-only chats and cloud runners without access to that Mac can research or prepare job files but cannot directly change its editor.

This is a separate skill. Keep `proof-first-video-editor` and `video-edit-fast` installed if they are working for you. This installer adds `video-edit-pipeline` and uses `~/.video-edit-pipeline/toolchain.json`; it never replaces their skill directories or configuration. The clone's dependency versions and reusable animation kit may be the same, while the skill name, job folder and bridge port are distinct.

From a checkout of this public repository:

```bash
python3 skills/video-edit-pipeline/scripts/setup.py install
python3 skills/video-edit-pipeline/scripts/setup.py fetch
python3 skills/video-edit-pipeline/scripts/run.py doctor
```

`install` links the skill into `~/.agents/skills/video-edit-pipeline`, documented by both Codex and Grok Build. It refuses to replace an existing skill. Keep the checkout: the installed skill points to it. Restart or refresh skill discovery in a running harness. `--harness grok` or `--harness claude` uses that product's private skill directory instead; one installation per harness is enough.

`fetch` clones three pinned MIT repositories under `~/.video-edit-pipeline/vendor/` and records their paths/commits in `~/.video-edit-pipeline/toolchain.json`. Existing Borumi tool installations are preserved. It patches the isolated legacy bridge to decline MCP elicitation, rather than automatically accepting it. User consent prompts must be resolved in the app. It does not start a bridge, change model settings, install npm dependencies, or touch video projects.

Run dependency scripts with environment resolved automatically:

```bash
python3 <skill>/scripts/setup.py run edit bridge/bridgectl.sh start
python3 <skill>/scripts/setup.py run edit bm --health
python3 <skill>/scripts/setup.py run edit bm list_open_projects '{}'
python3 <skill>/scripts/setup.py run proof borumi/snapshot.py --help
```

The new bridge defaults to loopback port 47813 so it does not replace an existing 47811 connection. Some agent terminals terminate background children after a command exits. If readiness disappears, keep `setup.py run edit bridge/bmcpd.py --port 47813` running in a retained terminal session, then reconnect and list projects again. All writers targeting the same project must still use **the same project work directory/lock**; a separate bridge does not isolate timeline mutations. Do not expose the local bridge publicly. A missing dependency or guide is a setup problem; do not improvise direct SQLite writes.

Only install heavier dependencies when the selected stage needs them: Pillow/numpy for inherited cards/writer frame checks; the animation kit's documented `doctor.sh --install` for Remotion; an existing whisper.cpp model only if Borumi lacks adequate timed transcription. Full installation details live in the pinned upstream README. Reuse working local installations when verified, rather than reinstalling to satisfy unrelated stages.

## Invocation and routing

| Harness | Invocation | Execution route |
|---|---|---|
| Codex | `$video-edit-pipeline` or select it via `/skills` | Local shell/FFmpeg and Borumi bridge; native subagents when supported |
| Grok Build | `/video-edit-pipeline` or natural request naming the skill | Same files and scripts; native subagents or sequential tasks |
| Claude Code | `/video-edit-pipeline` after `setup.py install --harness claude` | Same scripts; existing Workflow system is optional |
| Other local harness | Read `SKILL.md`, then follow linked references as needed | Needs local file/shell access and a way to view images; map its tools to these capabilities |
| Remote/chat-only harness | Read skill and a sanitized job packet | Return plans/assets; hand off writes to the Mac coordinator |

Set models with the harness's actual model selector/configuration. Grok accepts but ignores `model`/`effort` skill-frontmatter keys, so this package intentionally does not promise YAML model routing. Its native `--max-turns`, `--no-subagents`, `--prompt-file`, and `--reasoning-effort` can bound a task; inspect your installed `grok --help`. Codex supports noninteractive `codex exec`; inspect `codex exec --help` for your installed flags. Never paste flags that bypass approvals merely to save time.

[Model routing](model-routing.md) specifies responsibilities and current model examples. Grok Build's actual `[subagents.models]` setting is separate from ignored skill frontmatter; verify effective model assignments in the current harness. The installer does not change global routing. [Starter scenarios](scenarios.md) provides copyable prompts for each harness.

Checkpoints travel between harnesses as local folders. On handoff, pass `goal.md`, `checkpoint.json`, `scene-index.json`, `tasks.json`, only the relevant packet(s), and unresolved issues. Revalidate the current timeline before writing. A new provider's window does not erase another provider's quota or grant permission to buy API credits.

## Verified documentation

Checked 2026-10-16: [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Grok skills and plugins](https://docs.x.ai/build/features/skills-plugins-marketplaces), [Grok Build](https://x.ai/build). Local verification additionally used Codex CLI help and Grok Build 1.0.60 `inspect --json`; these are compatibility observations, not a guarantee about every harness version.
