# Model and worker routing

Official model and harness documentation checked **2026-10-16**. The assignments below are workflow recommendations to evaluate on real edits, not measured claims of equal video quality. Recheck available models in the active harness before dispatching work.

## Starting team

Use **one capable coordinator, up to two preparation workers, and one timeline writer**. The coordinator can also be the writer; these are responsibilities, not four mandatory agents. Reuse worker slots between stages. For a small edit, the coordinator alone is often faster. Add parallel workers only for independent work with a clear output and enough work to justify the extra context.

Keep the strongest model available for difficult decisions. It does not need to supervise every tool call. The routine coordinator and required final reviewer can be a capable middle model when it passes the quality gate.

## Concrete model choices

| Class | Verified examples | Recommended use |
| --- | --- | --- |
| Local code, no model | Python, FFmpeg/ffprobe, existing Borumi helpers, Remotion | Inventory, hashes, time conversion, range validation, subtitle remapping, rendering and receipt checks. Local execution does not consume inference tokens, although asking an agent to repeatedly supervise it does. |
| Small / inexpensive | **Claude Haiku 5.5** (`claude-haiku-5-5`), **GPT-6 Luna** (`gpt-6-luna`) | Extract candidate cuts or clips, discover possible sources, organize existing assets, and flag caption defects from a bounded packet. Outputs are proposals, not final editorial decisions. |
| Capable / balanced | **Claude Sonnet 5.5**, **GPT-6.1 Sol** (`gpt-6.1-sol`); **Grok 4.7** (`grok-4.7`) is another capable option when exposed by the harness | Make cut decisions, verify evidence, design and implement visuals, coordinate the job, review the finished output. This is a workflow grouping, not a claim that these providers have identical performance or pricing. |
| Escalation | **Claude Opus 5.5**, **GPT-6 Astra** (`gpt-6-astra`) | Resolve conflicting evidence, difficult narrative choices, repeated tool failures, unusual animation architecture, or a demanding final editorial review. Give it the disputed decision and evidence, not the entire production history. |

Haiku **5.5 is a real current release**, dated October 7, 2026. Anthropic describes it for extraction and subagent work, Sonnet 5.5 for everyday work, and Opus 5.5 for more complex work. Its documentation also lists Fable 5.1; this workflow does not require every higher tier. [Claude Haiku 5.5 model documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview).

OpenAI documents Luna for focused high-volume tasks, Sol for capable work at a lower cost than Astra, and Astra for demanding reasoning. These provider descriptions support the starting choices; they do not establish editing-quality equivalence. [GPT-6 model guidance](https://developers.openai.com/api/docs/guides/latest-model).

xAI currently recommends Grok 4.7 for code and general agent work. Do not invent a “cheap Grok worker” model name. If the signed-in Build session exposes only one suitable model, scope its packets tightly or run sequentially; a separate provider requires its own supported connection and billing check. [Grok model catalog](https://docs.x.ai/developers/models).

## Effort settings: choose them per responsibility

**Start a raw-to-finished job with Sol `high` or Sonnet `high` for the story, cutting strategy and style plan; use `medium` for routine coordination once that plan is settled.** Running two workers does not itself require `max`: dispatching bounded packets and checking dependencies is much simpler than resolving narrative ambiguity. A capable lead can avoid repair loops; keeping it off mechanical work and reserving premium models for hard decisions is the intended saving. Measure total accepted-work usage before calling this cheaper in practice.

Change the coordinator's effort between stages only when the host supports doing so cleanly. The user should not have to babysit phase-by-phase switches. Otherwise, keep the coordinator at `high`, explicitly set each worker's model/effort, and take the main savings from bounded packets, scripts, reuse and fewer retries.

These are recommended starting settings, not provider guarantees or automatic routing:

| Responsibility | Claude option | Codex option | Grok option | Why / when to change |
| --- | --- | --- | --- | --- |
| Initial story/cut/style plan; difficult task decomposition | Sonnet 5.5 `high` | GPT-6.1 Sol `high` | Grok 4.7 `high` | Decisions affect the whole video. Once the plan is coherent, return to the coordination setting. |
| Coordinate two workers; reconcile receipts and apply an accepted plan | Sonnet 5.5 `medium` | GPT-6.1 Sol `medium` | Grok 4.7 `medium` | The packets, stage gates and checks already define the work. Raise to `high` if results conflict or dependencies are unclear. |
| Cut/reel candidates, source scouting, caption findings | Haiku 5.5 `medium` | GPT-6 Luna `high` for multi-tool scouting | Grok 4.7 `medium` if no smaller suitable model is available | A cheaper worker still needs enough effort to follow the evidence/output contract. The coordinator owns acceptance. |
| Simple extraction/classification from supplied text | Haiku 5.5 `low` | GPT-6 Luna `low` | Grok 4.7 `low` | Clear, short inputs and machine-checkable outputs. Use local scripts first; return to the prior row when research or judgment is required. |
| Existing-template edits and serial timeline application | Sonnet 5.5 `medium` | GPT-6.1 Sol `medium` | Grok 4.7 `medium` | Well-specified implementation with previews and readback. Use `high` for a new animation system, difficult timing, or unexplained failures. |
| Cut acceptance, factual/proof acceptance and final editorial gate | Sonnet 5.5 `high` | GPT-6.1 Sol `high` | Grok 4.7 `high` | These decisions require continuity, context and actual media inspection. Preserve the full acceptance checklist. |
| Unresolved hard decision after capable review | Opus 5.5 `medium`, then `high` if needed | GPT-6 Astra `medium`, then `high` if needed | Grok 4.7 `xhigh` for the bounded unresolved problem | A stronger model at moderate effort is a useful first escalation. `xhigh`/`max` on Claude/OpenAI are exceptional comparisons when a concrete remaining defect warrants them. Grok 4.7 has no `max`. |

Supported values checked **2026-10-16**:

- Haiku 5.5, Sonnet 5.5 and Opus 5.5 each support `low`, `medium`, `high`, `xhigh`, `max`. Their API defaults are respectively `medium`, `high`, `medium`. Sonnet's official guidance recommends `medium` for well-specified agentic tool work and `high` for harder/longer work. [Claude effort reference](https://platform.claude.com/docs/en/build-with-claude/effort), [Sonnet calibration guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5).
- Luna supports `none`, `low`, `medium`, `high`, `xhigh`, `max`; Sol and Astra support `low`, `medium`, `high`, `xhigh`, `max`. Luna and Sol API defaults are `medium`. The `high` Luna worker choice follows Codex's subagent guidance; use `low` for simple extraction as OpenAI's selection guide suggests. Client-specific extras are not portable API values. [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [model/effort selection](https://developers.openai.com/api/docs/guides/model-selection), [Codex agents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- Grok 4.7 supports `low`, `medium`, `high`, `xhigh`, with API default `high`; reasoning cannot be disabled. The `medium` execution setting above is this workflow's proposed step-down to evaluate. [Grok reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning).

`high` on one provider is not the same reasoning budget, capability or quota usage as `high` on another; even version changes can recalibrate a scale. Effort is also separate from speed tier and number of workers. Keep Standard speed, bounded inputs and explicit effort; raise effort for a demonstrated quality gap, not for every render, poll or status update. Lowering effort never removes playback, factual verification or receipt checks.

## Responsibilities and handoffs

Run cutting before final visual timing. Source discovery can overlap cutting for claims likely to survive; defer polished visual production and paid generation until the cut and claims are accepted. This prevents repeatedly retiming or discarding finished visuals.

| Stage / owner | Input and tools | Required output | Boundary / escalation |
| --- | --- | --- | --- |
| Intake — local scripts | One live snapshot, existing timed transcript, media metadata; `run.py`, `ffprobe`, hash tools | Scene packets, source/timeline mapping, asset inventory | Stop on missing media, inconsistent units, or stale project revision. Do not invent timings. |
| Cut scout — small worker A | One scene or bounded transcript section; local silence measurements and source playback when available | Timestamped retake, repetition, pause and reel candidates with a reason and uncertainty | No deletion authority. Escalate jokes, emotional pauses, competing takes, incomplete sentences, or unclear audio. |
| Editor — capable coordinator | Candidates, adjacent context, actual audio/video | Accepted cut plan, preserved context and exact source ranges | A timestamp proposal is not a good cut until delivery and continuity are checked. Escalate unresolved narrative alternatives. |
| Cut application — single capable writer | Accepted plan, current snapshot, Borumi transaction helpers | Backup, staged change, preview/readback and cut revision | No other agent writes the timeline. Reject stale hashes; inspect joins and audio before treating the cut as locked. |
| Source scout — small worker B | Likely claims before cut review, retained claims afterward, and cached-source index; search, browser, optional Firecrawl/X search | Up to three canonical source candidates per claim, short supporting passage, date, URL, capture pointer and uncertainty | Discovery only. No fabricated tweet images, verified badges, numbers or engagement counts. A search snippet is not proof. |
| Evidence reviewer — capable coordinator or worker | Actual source page and captured pixels, exact spoken claim and date | Claim-to-source acceptance or a concrete correction / missing-proof finding | Check identity, dates, context and screenshot fidelity. Escalate conflicting primary evidence; a stronger model cannot replace missing evidence. |
| Visual builder — capable worker | Locked cut revision, accepted proof, style reference, reusable templates | Asset manifest, timed layout plan and local preview; new template code only where needed | Reuse before generation. Local tools perform renders. Optional Higgsfield generation needs a specific shot brief and existing spending authorization. |
| Captions and technical QA — local scripts + small worker | Final timing, transcript, rendered preview; subtitle checks, frame sampling, loudness/duration tools | Timecoded findings for spelling, names/numbers, caption overflow, missing assets and technical defects | Flag uncertain words; do not silently rewrite meaning. Transcript checks cannot prove playback or visual quality. |
| Assembly and final gate — single writer + capable reviewer | Accepted assets, cut revision, QA findings, actual export playback | Verified timeline readback, watched/heard deliverable, closed findings and remaining limitations | Review story, proof readability, crop, pacing, sound and joins. Escalate difficult final decisions to Opus/Astra; never waive the gate to save usage. |

If the cut changes after visual work starts, invalidate and rebuild only the affected timing, captions, visuals and exports. Preserve valid research and unchanged assets. Use the [job receipt and reopen protocol](jobs.md).

## A worker contract that stays small

Give every worker the goal, role, exact scene/source revision, relevant packet, tools it may use, output path, and stopping conditions. Do not fork the complete history by default when the harness allows a fresh context.

Starting bounds, adjustable by the coordinator:

- One scene or at most five minutes of transcript per candidate task. Return at most five cut candidates or three reel candidates.
- One claim cluster per source task; eight external tool calls, then return findings and gaps. Cache each useful page/capture locally.
- One attempt and one focused correction; after the same defect recurs, escalate the bounded task instead of repeating a cheap loop.
- Return a structured artifact and a summary under 500 words. Store full captures and evidence in files.
- No nested delegation, live timeline edits, or extra paid jobs for preparation workers. Enforce tool restrictions in the harness where supported; prompt instructions alone are not a security boundary.

Escalate immediately for contradictions, unsupported numeric claims, uncertain time mapping, missing input, or a tool capability the worker lacks. “Incomplete with evidence” is better than confidently marking an unverified step done.

## Make model selection real in the harness

These role names and any pipeline `model_class` fields are advisory. This skill's job runner does **not** launch models or change subscriptions. Before claiming a cheaper worker ran, verify the resolved settings in the harness's task/session details. Record `requested_model`, `actual_model`, `requested_effort`, `actual_effort`, credential route and any fallback in the private receipt/log; use `unknown` when the host does not expose a resolved value. Never log keys.

| Harness | Native mechanism | Portability limit |
| --- | --- | --- |
| Codex | Set both `model` and `model_reasoning_effort` in a custom agent TOML, or use the host's supported spawn fields. `[agents]` defaults can set `default_subagent_model` and `default_subagent_reasoning_effort`. | Custom agent fields take precedence over resolved spawn/default settings. Parent settings can otherwise be inherited. A host may restrict model overrides or full-history forks; use its actual schema. Provider, permissions and account access still apply. |
| Claude Code | Custom subagent `model` and `effort` fields; supported per-invocation overrides. Use a full model ID for reproducibility. | Per-invocation effort needs v2.1.292+; `CLAUDE_CODE_EFFORT_LEVEL` overrides it and the agent field. Without an override, the session effort applies. Check `/tasks` and any model-substitution warnings. |
| Grok Build | `[subagents.models]` maps agent types to model IDs; session `-m` and `--effort` choose model/effort. Custom model settings expose `reasoning_effort` when supported. | The per-agent model map alone does not prove per-agent effort. Verify the resolved child setting; use an explicitly configured separate session if the host cannot set it. Skill frontmatter `model`/`effort` is ignored. Built-in `explore`/`plan` cannot render because they lack shell/edit tools. |
| Other / one-model harness | Execute the same role packets sequentially, or use its documented model selection | State the limitation. A role label does not prove mixed-model execution or tool access. |

Configuration references: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Claude Code model and effort selection](https://code.claude.com/docs/en/sub-agents), [Grok per-agent configuration](https://docs.x.ai/build/settings/reference), [Grok CLI effort flag](https://docs.x.ai/build/cli/reference), [Grok skill field behavior](https://docs.x.ai/build/features/skills-plugins-marketplaces), [Grok child-session tool limits](https://docs.x.ai/build/features/subagents), [Grok session/custom-model configuration](https://docs.x.ai/build/overview). Checked 2026-10-16; the package does not silently overwrite these user settings.

**Set model and effort together for every dispatched role.** A worker labeled “cheap” can still inherit the lead's premium model or high effort. If the host cannot honor a requested combination, record the actual fallback and keep the task bounded; do not report mixed-model savings. On resumed workers, check the effective settings again. No prompt text can override a host's supported model list or credential policy.

## Optimize the correct allowance

API dollars per token do not directly measure subscription quota. Record accepted output quality, elapsed time, actual usage-meter change where available, repair work, and extra service spend separately. Parallel agents on one account share its allowance; they do not multiply it. Switching providers only helps when the saved checkpoint prevents repeated work.

Use Standard speed as the starting point. OpenAI distinguishes included plan usage from purchased-credit rates and API-key billing; faster service tiers can consume more included capacity. [Codex pricing and usage](https://learn.chatgpt.com/docs/pricing).

Claude's Pro/Max allowance is shared across Claude and Claude Code, and an API-key authentication route can change billing. Grok describes a shared weekly product pool, with its usage screen also listing API. Check the effective credential and meter rather than assuming a provider key is included. [Claude plan usage](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), [Grok usage FAQ](https://docs.x.ai/grok/faq).

Adopt a cheaper route only when representative cut, proof and reel tasks meet the same acceptance criteria with less total usage or waiting **including corrections**. If it fails, retain the capable model for that responsibility. See [the quota workflow](quota-workflow.md) for the broader production process.
