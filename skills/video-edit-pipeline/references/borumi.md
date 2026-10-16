# Borumi editing operations

Use the pinned `proof-first-video-editor` writers through `setup.py run`. The new skill changes orchestration and scope; it does not reimplement Borumi transactions. Consult **only the upstream reference for the current operation**. Do not load the entire upstream SKILL plus every workflow into each worker.

## Read once

Resolve the exact project with `edit bm list_open_projects '{}'` or `edit find_project.py '<name>' --dry-run`. Short project IDs are connection-scoped; resolve them again on the new bridge. Get current state before using a remembered ID. The editor's rendered output and live `get_scenes`/timeline are authoritative.

For an authorized edit, `find_project.py '<name>' --open --ensure-backup` can open the project and preserve a raw duplicate. Inspect its reported paths and reused backup. A raw copy is useful only if it contains the source recordings. Do not duplicate the project on every resume. Use the existing work directory if another writer already owns it.

```bash
# Global snapshot options precede its subcommand.
python3 <skill>/scripts/setup.py run proof borumi/snapshot.py \
  --work '<project work>' --project-id '<current ID>' save '<job>/snapshot.json'
python3 <skill>/scripts/setup.py run edit dump_transcript.py --work '<project work>'
python3 <skill>/scripts/run.py ingest '<job>' --snapshot '<job>/snapshot.json' \
  --transcript '<project work>/transcript'
```

The existing transcript export contains timed per-scene words and blocks. Do not send every scene's words to every worker. Avoid retranscribing recordings already transcribed by Borumi; forced alignment is only for a demonstrated timing problem. Offline database inspection is diagnostic only: media transcript times are source seconds, not project milliseconds; overlays may extend beyond their owning scene, and some durations are null. Never sum all segment durations to infer a project's length.

## Writer contract

One writer at a time across **all** harnesses for a project. Use the inherited lock and transaction implementation, including project-wide before/after diff and base-hash collision check. Every new write is staged with `--dry`, its check table and rendered frames inspected, then repeated without `--dry` after verifying unchanged live state. The receipt must identify project, base hash, resulting hash, operation, and checked artifacts.

The pinned writers' exit codes: 0 success/dry success; 2 validation failed/aborted; 3 error/aborted; 4 concurrent-change collision/aborted. A collision invalidates the plan. Do not undo or overwrite the creator's edits to make an old plan pass. On unknown completion or timeout, read the timeline and receipts before retrying.

Use the upstream `references/borumi-writer.md` for each selected operation:

| Work | Existing script(s) | Critical constraint |
|---|---|---|
| Baseline/gaps | `borumi/snapshot.py` | Read project-wide state once at batch boundaries; poll compact hash/state with backoff |
| Raw retake cuts | edit toolkit `apply_cuts.py` | `--no-layout-fix`; dry-run; last scene first; preserve synced layers |
| Canvas/base layouts | `borumi/canvas.py`, `base_layouts.py` | Do not reapply base layouts over existing designed ranges |
| Cards/badges | `borumi/make_card.py`, `chapter_card.py`, `step_badges.py` | Use existing timed words; inspect frame boundaries and source order |
| Visual placement | `borumi/place_render.py`, `swap_render.py` | Check the script's `--help`; alpha FRONT and background BEHIND have different contracts |
| Export/tighter cut | upstream delivery/tighten scripts | Never export during an active transaction; range map must follow the final cut |

Names and flags come from the pinned scripts' `--help`, not guessed JSON. If a listed operation is unavailable in another version, inspect its actual scripts and guide. Do not hand-call `delete_scenes`, delete recordings, `untrim_segments` on layouts, or delete content segments: the existing package documents project-wide layout rebuild hazards.

## Minimize repeated render work

Plan independent changes first; combine compatible changes into a coherent reviewed scene batch. Keep the inherited checks at mutation boundaries. Cache immutable source records and stage outputs between batches, but never substitute a cached timeline for the required live conflict check. A 10-second polling loop that reads the entire project is not a productive agent. Wait on a render job once, process its terminal result, then validate the artifact.

If the user is actively editing, defer that project's writer and continue independent research/assets. A persistent collision needs coordination, not more parallel writers.
