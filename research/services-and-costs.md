# Faster video editing without exhausting one model plan

Research checked **2026-10-16**. Prices below are USD snapshots, not quotes. Official documentation was opened and read; no paid generation or inference was run for this research. The recommendations are an engineering proposal to benchmark on representative edits, not a claim that cheaper models have already matched an existing finished video.

## Success metric: quality per unit of plan usage

The primary objective is an equally good accepted video using less subscription capacity and less waiting, not the lowest dollar price per generated draft. Reduce duplicated context, unnecessary tool loops, and repeated renders first. Preserve the strong editorial pass and the finished-export checks. A smaller model is an optional optimization only after its outputs pass the same acceptance criteria; measure correction work as part of its cost. The dollar examples later in this report are secondary illustrations, not the routing objective.

## Recommended starting point

Use the subscriptions and media already available: a local Codex or Grok Build session, the Borumi connection, existing project transcripts, FFmpeg, a reusable asset folder, and a compact edit plan. Use Firecrawl when a source needs research or capture. Use the existing Higgsfield plan connection only for shots that need generation. Do not buy another service before measuring this workflow.

The target is **$0 additional service spend while staying inside existing allowances**, not free computing or unlimited usage. Subscription fees, local storage/electricity, opportunity cost, consumed plan credits, and eventual overages remain real costs. Set separate limits for incremental dollars and existing generation credits; one is not a substitute for the other.

The most valuable optimization is to stop asking an expensive model to repeatedly read the whole project, rediscover the same sources, poll jobs, and perform mechanical edits. A small model can suggest candidates from a bounded transcript excerpt. A script can validate time ranges. A stronger model can make the editorial decision. One agent applies it and verifies the resulting frames and sound.

## What actually runs the skill

| Surface | Appropriate role | Installation and limits |
| --- | --- | --- |
| Local Codex CLI / compatible desktop session | Read local media, call Borumi tools, run helpers, coordinate review | Current docs discover user skills under `~/.agents/skills/`; invoke with `$video-edit-pipeline` or select using `/skills`. Repo discovery uses `.agents/skills`. |
| Official Grok Build | The same local workflow, including skills and MCP | Discovers `~/.agents/skills/`, `~/.grok/skills/`, and repo `.grok/skills/`. User-invocable skills appear as `/video-edit-pipeline`. Check discovery with `grok inspect`. |
| Grok in a normal browser chat | Research, script alternatives, feedback on supplied material | A chat upload alone does not establish access to local Borumi. Use the local agent or an explicitly configured connector/tunnel and verify its capabilities. |
| Other tool-capable harness | Execute the same artifact contracts | Read `SKILL.md`, provide local execution and the needed Borumi/MCP tools, and use that harness's documented discovery/invocation. A Markdown file cannot itself grant tools or permissions. |

These paths and invocations come from [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) and [Grok Build's skill documentation](https://docs.x.ai/build/features/skills-plugins-marketplaces), accessed 2026-10-16. The latter also says Grok accepts but does not apply `model` or `effort` skill-frontmatter keys: model routing must be configured in the harness, not assumed from YAML. [Grok Build's overview](https://docs.x.ai/build/overview) documents local, headless, ACP, browser sign-in, API-key, and custom-model routes.

## Protect the right allowance

| Provider | Current official distinction | Practical rule |
| --- | --- | --- |
| Claude | Pro/Max usage is shared across Claude and Claude Code, with five-hour and weekly limits. An `ANTHROPIC_API_KEY` can select API billing instead of subscription usage. Included monthly API credits on eligible plans do not pay for Claude Code extra usage. | Keep Claude for the editorial pass where it adds value. Check the effective login route; do not silently switch to API billing when the plan is exhausted. |
| Codex | ChatGPT sign-in uses plan allowance; API-key sessions follow API pricing. Local/cloud agent usage is shared. Current docs say Pro has no five-hour limit, while weekly limits can still apply. | Use Standard speed by default. Check `/status` and the usage dashboard rather than guessing an account's capacity from the plan name. |
| Grok | The current consumer FAQ describes a shared weekly allowance across products including Build; its usage UI also lists API. Grok Build supports browser sign-in and API-key authentication. | Verify which account, credential route, and meter apply. Do not assume an arbitrary xAI API key or third-party provider is covered by a SuperGrok subscription. |
| Higgsfield | MCP and the ChatGPT plugin use the connected plan's credits; its developer API has a separate dollar balance. | Prefer the existing plan connector for occasional shots. Treat direct API integration as a separate billing choice. |

Sources: [Claude plan usage](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), [Codex pricing and limits](https://learn.chatgpt.com/docs/pricing), [Grok usage FAQ](https://docs.x.ai/grok/faq), [Higgsfield API versus plan connections](https://higgsfield.ai/blog/higgsfield-api), accessed 2026-10-16.

Two easy mistakes consume capacity quickly. Current Codex documentation lists **2.5× included usage for Fast mode and 8× for Astra/Sol Ultrafast** versus Standard; that is a quota tradeoff, not free speed. It also says credit prices alone do not determine included subscription consumption. Likewise, launching four workers on one account does not create four allowances. Parallelism shortens elapsed time only when tasks are independent and the service has capacity.

## Divide the work by difficulty

| Work | First choice | What the stronger model reviews |
| --- | --- | --- |
| File inventory, hashes, duration, dimensions, timeline bounds | Local code and `ffprobe` | Only anomalous results |
| Transcription | Reuse project transcript; local Whisper if missing | Names, numbers, technical vocabulary, meaning-changing errors |
| Retake and silence candidates | Local measurements plus a small model over the relevant excerpt | Delivery, comedic/dramatic pauses, sentence continuity |
| Source discovery | One bounded research worker using search tools | Exact claims, dates, context and source reliability |
| Reel candidates | Small model returns a few timestamped self-contained clips | Hook, payoff, context, cuts and crop feasibility |
| Overlay and layout construction | Reusable templates and deterministic transforms | Legibility, visual hierarchy and whether evidence appears when discussed |
| Borumi mutations | One coordinator using current tool schemas | Changed scene preview and timeline readback |
| Final editorial review | Balanced/strong model plus actual playback | Story, proof, voice, sound, visual errors and intended deliverables |

For current OpenAI models, start small, use GPT-6.1 Sol for synthesis or ambiguous edits, and escalate exceptional problems to GPT-6 Astra. This is consistent with the official [GPT-6 model roles](https://developers.openai.com/api/docs/guides/latest-model). It does not establish editorial parity; run the comparison below. Grok Build is a practical alternative when its allowance is available. Select an actually available model from the harness instead of hard-coding a retired name.

Keep a compact handoff: goal, constraints, project revision, relevant source ranges, accepted decisions, output paths and remaining work. Give each worker one question, an output schema, a small input slice, and a stopping condition. Save full evidence to files; return only findings and pointers to the coordinator. Load service references only when needed.

## Parallelism that saves time

Start with **one coordinator and up to two independent workers**, constrained by the host and plan. A third worker is an option only after measured capacity and budget justify it. Research, reel selection and source-media analysis can overlap. Keep timeline writes serial. A worker should return suggestions or files, not race another writer in a live project. Grok's documented [subagents](https://docs.x.ai/build/features/subagents) have independent contexts, so duplicated instructions and history are additional work.

Recommended operating rules:

1. Reuse prior results by project/media hash and source URL. Do not fan out identical research prompts.
2. Set a maximum output size, tool-call count, attempts and elapsed time per worker. Avoid nested delegation for routine tasks.
3. Begin with at most two requests per external service. Raise only after actual latency and throttling show spare capacity; provider limits are ceilings, not recommended targets.
4. On throttling, honor `Retry-After` or use exponential backoff with jitter. Stop a provider's queue when its allowance is exhausted and checkpoint the work. Cached tokens can still count toward xAI token-rate limits, according to its [rate-limit documentation](https://docs.x.ai/developers/rate-limits).
5. Store a generation job ID before waiting. Poll the existing job; a timeout is not proof that submission failed. Reconcile status before any repeat that could charge again.
6. If a weak model needs repeated explanations or repairs, escalate the bounded task once. Repeated cheap failures can cost more in review time than one good answer.

For example, three truly independent ten-minute analyses can approach ten minutes plus coordination rather than thirty; this arithmetic is not a measured speedup. Shared GPU rendering, service queues, or serial timeline writes can erase the gain. Measure end-to-end elapsed time, not just token speed.

## Dated API examples, separate from subscription value

The following is **aggregate token arithmetic** for 200,000 uncached input tokens and 20,000 total billed output tokens, distributed across short-context requests. Output assumptions must include billed reasoning. It excludes tools, media, cache writes, retries, taxes, regional surcharges and storage. Each request must remain below its model's long-context threshold; sending one 200k-token prompt to xAI would trigger different rates.

| Model | Input / million | Cached input / million | Output / million | Example total |
| --- | ---: | ---: | ---: | ---: |
| GPT-6 Luna, Standard | $0.10 | $0.01 | $0.50 | $0.03 |
| GPT-6.1 Sol, Standard | $2.00 | $0.10 | $10.00 | $0.60 |
| GPT-6 Astra, Standard | $10.00 | $1.00 | $50.00 | $3.00 |
| Grok 4.3 | $1.25 | $0.20 | $2.50 | $0.30 |
| Grok 4.7 | $2.00 | $0.50 | $6.00 | $0.52 |

Sources: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), [xAI API pricing](https://docs.x.ai/developers/pricing), accessed 2026-10-16. These are billing examples, not an assertion that every model is available in every subscription or that all produce equally good edits.

If 80% of this work succeeds with Luna and 20% requires Sol, the arithmetic becomes **$0.144 instead of $0.60**, a 76% reduction in this limited token scenario. If a further 20% of the original workload must be repeated on Sol, it becomes **$0.264**, a 56% reduction. Extra review time or larger outputs may overturn the result. Moving work from an included subscription to a paid API can also increase actual cash spend even when the API rate is low.

Prompt caching is secondary to avoiding the request entirely. Maintain a stable prefix and reuse results locally. OpenAI's current rate card includes cache-write charges, while its Codex credit billing does not have a separate cache-write charge. Use the returned usage record rather than estimating cache hits from similar prompts. For nonurgent offline evaluations or bulk labeling, [OpenAI Batch](https://developers.openai.com/api/docs/guides/batch) offers a 50% discount with a 24-hour completion window; it is unsuitable for interactive timeline decisions.

## Research, tweets and reusable proof

Use a claim list before search. Search a few precise queries, rank the results, fetch only the selected sources, and save the canonical URL, author, publication date, access date, supported claim and local capture. Preserve a compact transcript excerpt or quote with context. This makes the asset reusable in a long-form edit and its reels.

Firecrawl currently lists **1,000 free credits/month** and a **$19/month Hobby plan with 5,000 credits**; annual billing has a different effective price. It can also be used through an already connected account. Do not add a paid plan for this workflow unless actual demand exceeds the existing allowance. [Firecrawl pricing](https://www.firecrawl.dev/pricing), accessed 2026-10-16.

Its [search documentation](https://docs.firecrawl.dev/features/search) prices ordinary search at 2 credits per ten results, rounded up, with extra charges when the results are scraped. Its [scrape documentation](https://docs.firecrawl.dev/features/scrape) lists one credit for a basic page, four extra for JSON mode, and one credit even for a cached page. A local saved copy avoids that repeat call. Check the page's metadata status and content, not only the API's successful HTTP response.

A sample pack of ten searches returning up to ten results each and twenty basic page scrapes costs **40 credits** before special formats, provider-routed data, screenshots requiring other operations, or retries. Prefer plain Markdown and local structured extraction when sufficient. Do not request paid LLM extraction or whole-site crawling by default.

[xAI X Search](https://docs.x.ai/developers/tools/x-search) supports post and thread discovery. Its current charge is **$5/1,000 posts fetched and $10/1,000 profiles fetched**, in addition to tokens. Parent and quoted posts count. Twenty posts and two profiles therefore add $0.12, not one search-call fee. Bound the discovery to the topic/date/author before enabling it.

For on-screen tweets, discovery is only the first step. Open the original post, verify the handle, exact text, date and thread context, then capture a legible representation with provenance. A Firecrawl screenshot can be a login page, a stale result or the wrong post. Inspect it. Never render invented text as an authentic tweet; label any designed excerpt/recreation. Keep source verification and rights/reuse decisions distinct.

## Generated footage: buy only the missing shot

First try existing footage, screen capture, a genuine source capture, or a simple animated diagram. Generate only when motion itself communicates something those assets cannot. Approve the shot's purpose, duration, framing, reference assets and final placement before submitting it. Generate one preview, review it in context, then decide whether additional variations are justified.

Higgsfield is the preferred optional generation layer when an existing connected plan has authorized credits. The [official API explanation](https://higgsfield.ai/blog/higgsfield-api) confirms that developer API billing is separate and that completed media should be downloaded for long-term retention. Its [credit guide](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work) explains that plan credits reset and generation cost depends on model, duration and resolution. It says website Unlimited/free allowances do not generally cover automated tools; current connector contracts also expose specific free/unlimited paths. Do not infer eligibility from a plan label: use the live quote and entitlement response. Do not invent a universal dollar-per-credit conversion.

The installed Higgsfield connector contracts inspected during this research expose model discovery, per-model schemas, cost estimates, submission and grouped job waiting. Important detail: an estimate with an HTTPS image reference may import that image into the media library. A price-only check should omit private references; a full preflight should reuse already confirmed media IDs. A quote does not mean a video exists, and a completed generation does not mean it has been inserted into Borumi.

For a separate xAI API illustration, [Grok Imagine Video 1.5 Lite](https://docs.x.ai/developers/models/grok-imagine-video-1.5-lite) lists $0.03/second for 720p and [Video 1.5](https://docs.x.ai/developers/models/grok-imagine-video-1.5) lists $0.14/second for 720p, checked 2026-10-16. Eight five-second shots with three completed attempts each are **120 generated seconds: $3.60 or $16.80**, plus media inputs and other applicable fees. That is generation volume, not final-video duration. Measure cost per accepted shot and inspect motion/text/identity consistency; lower sticker price does not imply lower production cost.

## Local media work and optional services

Reuse Borumi's transcript before paying to transcribe again. [whisper.cpp](https://github.com/ggml-org/whisper.cpp) supports local transcription with Apple Silicon acceleration. Local execution spends no provider inference credits, but runtime and accuracy depend on model, machine and audio. Benchmark a representative noisy passage and names before choosing a small model. Keep the master audio untouched.

[FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) support silence analysis, trims, crops, overlays and measured loudness normalization. Use them for deterministic preparation, proxies and checks. Silence is only a cut candidate, and loudness normalization is not a replacement for denoising or listening. Avoid exporting every intermediate at full resolution; validate proxy frames, then render the accepted result once and check the real export.

[Auphonic pricing](https://auphonic.com/pricing) offers two free processed hours per month, but free productions contain its jingle. It is optional for difficult audio where saved repair time justifies the cost. Do not introduce it into otherwise clean recordings merely because automation exists.

“Eden” is ambiguous. [Eden AI](https://www.edenai.co/feature/video-generation) is an API aggregation option; [Eden.art](https://eden.art/) is a different generative-agent product. Neither is required here. Eden AI's [cost page](https://www.edenai.co/reduce-token-costs) describes a 5.5% fee when buying credits. Its advertised savings are not evidence of savings on these videos. Select it only after identifying the intended service and comparing the exact model, output, fee and operational benefit against the existing connections.

## How to prove this is better

Run a small acceptance comparison on three representative excerpts: a talking-head retake, a research/tweet overlay, and a screen-recording explanation with a vertical reel. Use the same source ranges and requested outcome for the current workflow and the proposed route. Keep private footage and account information out of the public repository.

Record elapsed time to accepted edit, human correction minutes, provider/model/speed, available quota before and after when exposed, billed token/tool/credit usage, rejected assets, retries and export defects. Score narrative continuity, source accuracy, caption names/numbers, crop/legibility, sync and audio quality. A cheap pass counts only when it meets the same acceptance criteria. Report “not measured” rather than converting hidden subscription quota into invented dollars.

Promote the cheaper route per task type only when total time and/or incremental cost improve without a material quality regression. Keep difficult cases on the stronger route. This preserves the editing standard while making the savings measurable and repeatable.
