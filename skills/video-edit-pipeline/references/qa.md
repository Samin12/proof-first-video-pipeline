# Evidence of completion

Choose checks that match the edit. Do not replace editorial review with dozens of duplicate reviewers, but do not skip the evidence needed to know the edit worked.

| Deliverable | Required observation |
|---|---|
| Narrative/cut | Read kept text; listen to cut boundaries and important pauses; confirm intended meaning and all requested beats |
| Proof visual | Exact source supports claim; rendered text/numbers match; source remains readable at intended viewing size |
| Borumi write | Correct project; backup with source coverage; staged diff/frames; current base hash; committed readback |
| Compositing | No hidden proof/camera, wrong source order, full-frame alpha errors, empty panels, or visible flashes |
| Audio | No missing voice, clipped joins, new drift, unintended music or processing artifacts |
| Captions/chapters | Names/numbers corrected; words and chapters mapped to this final cut; no trailing cues |
| Reel | Hook and payoff make sense alone; meaningful source crop, readable cards/captions, clean ending, correct orientation |
| Export | File exists and decodes; dimensions/fps/duration/audio match brief; review actual exported file |

For a full edit, continuously review the final export with audio. For a small targeted change, review all changed intervals and their boundaries plus representative unchanged intervals; disclose if the whole video was not reviewed. If the current harness cannot listen or play video, save a review proxy and timestamped checklist and label the output as awaiting audio/playback review. A contact sheet proves sampled frames only.

`run.py verify` checks local structure, dependencies, receipts and hashes. It deliberately returns `deliverable_verified: false`. A worker can assert that it reviewed something, but the script cannot prove that assertion. Record concrete artifacts and observations; do not turn an empty text file called `visual_review.txt` into evidence of review.

Use one independent final reviewer for a full edit when available; send the final export, brief and unresolved issue list. Add a specialist reviewer only for a real unresolved issue. Do not ask several agents to independently rediscover the whole project by default.

Measure improvement on the **same scene and requested outcome**, using separate duplicates and identical acceptance criteria. Log elapsed time, human correction time, requests, input/output/cached tokens when available, actual billing route, provider credits, render attempts and accepted quality. Compare: current workflow; portable workflow on a balanced model; portable mixed small/balanced model. Do not equate file-size reduction with token savings, or fewer local tool calls with fewer paid model calls. Stop calling a model cheaper if repair and review outweigh its savings.

Final report: outputs and hashes, what changed, what was reviewed, remaining issues, actual measured cost/usage or `unknown`, and next action. Preserve drafts and source media. Publishing a skill repository and publishing a user's video are distinct permissions.
