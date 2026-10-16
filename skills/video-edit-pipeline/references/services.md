# Service routing and cost controls

Checked **2026-10-16**. Refresh prices, models, tool schemas and account entitlement before paid use. This reference describes optional capabilities; it does not install a connector, grant permissions, or authorize new purchases. Use existing authorization and budgets; do not ask again for every action already covered by them.

Quality is the gate. Optimize quota consumed and elapsed time per accepted edit; do not downgrade the editorial model simply because an API token is cheaper. Remove repeated work first, then benchmark model substitutions.

## Default route

1. Reuse local project data, transcripts, recordings and verified source captures.
2. Run deterministic inventory, time-range validation, proxy and media checks locally.
3. Use the current local Codex or Grok Build subscription session for bounded reasoning. Confirm its effective authentication and usage meter.
4. Use Firecrawl for selected external sources; save reusable evidence locally.
5. Use the existing Higgsfield plan connection only for a required generated shot within its authorized credit budget.
6. Add a paid API, Eden or audio service only when the exact need and incremental cost justify it.

Keep incremental USD and provider credits as separate budgets. Default incremental spend is zero unless the task already authorizes a larger amount. Never quietly fall back from an exhausted plan to a metered API or change auto-top-up settings.

## Models and concurrency

Choose a small available model for transcript labels, extraction, candidate reels and mechanical checks. Use a balanced model for editorial synthesis and a stronger model for unresolved quality problems. Current OpenAI examples are GPT-6 Luna, GPT-6.1 Sol and GPT-6 Astra respectively; recheck availability. These are starting assignments, not measured equivalence. [Official model roles](https://developers.openai.com/api/docs/guides/latest-model).

Use Standard speed by default: current Codex Fast mode consumes 2.5 times included usage, and Astra/Sol Ultrafast eight times. Subscription allowance is not calculated directly from the API rate card. Check `/status` or the dashboard. [Codex limits](https://learn.chatgpt.com/docs/pricing).

Start with at most two independent workers plus a coordinator, subject to the harness's capacity. Add a third only when measured capacity and budget justify it. One agent writes to Borumi. Give workers bounded source ranges, artifact outputs and stopping conditions; avoid repeated full transcripts and recursive delegation. Begin with two simultaneous requests per external service, respect lower live limits, back off on throttling, and checkpoint on exhaustion. A second worker on one account does not supply another allowance.

For paid APIs, record actual model, input/cached/output/reasoning usage, tool calls, attempts and charged cost when available. Current xAI cached tokens still count toward token throughput limits. [xAI rate limits](https://docs.x.ai/developers/rate-limits). Prefer local artifact reuse to paid repeated retrieval. Offline [OpenAI Batch](https://developers.openai.com/api/docs/guides/batch) can halve API token prices but permits a 24-hour turnaround; reserve it for noninteractive work.

## Harness checks

The portable user install path is `~/.agents/skills/video-edit-pipeline/`. Current [Codex docs](https://learn.chatgpt.com/docs/build-skills) support `$video-edit-pipeline` or selection through `/skills`; [Grok Build docs](https://docs.x.ai/build/features/skills-plugins-marketplaces) support `/video-edit-pipeline`, native `.grok/skills` paths and the shared user directory. Use `grok inspect` to check discovery. Grok ignores skill-frontmatter `model` and `effort`; enforce routing through supported harness settings.

Normal browser chat does not establish local Borumi access. Verify local execution, Borumi tools, filesystem access, and the active project's identity before promising an applied edit. A remote connector requires its own verified setup.

[Claude's plan guide](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) says Claude and Claude Code share five-hour/weekly usage and an API-key environment variable can select separate billing. [Grok's FAQ](https://docs.x.ai/grok/faq) describes shared weekly usage across products and includes API in its usage breakdown. Verify the actual key/login route; do not infer that every developer API credential is subscription-covered.

## Firecrawl and tweet evidence

Discover the current connector tools; prefer search with a small result limit, then scrape the selected URLs as Markdown. Do not default to whole-site crawling or paid LLM extraction. The current [search rate](https://docs.firecrawl.dev/features/search) is two credits per ten results rounded up; [basic scrape](https://docs.firecrawl.dev/features/scrape) is one credit, including cached results. JSON extraction adds four credits. Plan allowances and overages are in [Firecrawl pricing](https://www.firecrawl.dev/pricing).

Save canonical URL, author, date, access time, supported claim, capture path and hash. Check target-page status and actual content. Local saved evidence prevents repeated charges; provider-side caching alone does not.

[xAI X Search](https://docs.x.ai/developers/tools/x-search) discovers posts and threads. It currently bills per fetched post/profile plus tokens, so broad thread searches may expand cost. Verify the original post's exact text, handle, date and context, then inspect the saved capture. A screenshot of a login wall, search snippet or wrong post is not evidence. Label designed excerpts/recreations; never invent an authentic-looking tweet.

## Higgsfield

The connected plan's MCP/plugin spends plan credits; the [developer API](https://higgsfield.ai/blog/higgsfield-api) is separately billed in dollars. Do not convert credits to dollars using a guessed universal rate. Do not assume website Unlimited/free allowances transfer to automated tools: the [credit guide](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work) restricts them, while current connector contracts expose specific eligible paths. Verify the exact live entitlement and quote before selecting such a route.

Discover capabilities matching this sequence, rather than assuming a tool prefix:

1. Read existing assets and model catalog; select the needed shot and the model's actual supported duration, resolution, ratio and input roles.
2. Read balance/preferences if available. Get a quote for exact parameters and check the authorized credit cap.
3. Reuse confirmed media IDs. The current `estimate_video_cost` contract can import HTTPS image references; omit private references for price-only research. A quote does not validate all inputs.
4. Submit one preview and persist the returned job ID. Wait on that job using grouped waiting/status tools and their suggested delay. Reconcile a timeout before resubmission.
5. Download the completed media, inspect frames and audio, record dimensions/duration/hash, then insert and preview it in Borumi. A job marked complete is not an applied edit.

Current connector capability names include `models_list/search/get`, `estimate_video_cost`, `generate_video`, and `jobs_wait`; availability and schemas vary by host. Check the live contract. Limit creative attempts; compare cost per accepted shot, including discarded completed generations. Preserve any required provenance labels.

## Local tools and optional additions

- [whisper.cpp](https://github.com/ggml-org/whisper.cpp): local transcription with Apple Silicon support. Reuse the project transcript first; review names, numbers and a sample of timing before bulk use.
- [FFmpeg](https://ffmpeg.org/ffmpeg-filters.html): local proxies, silence candidates, crop/overlay preparation and loudness analysis. Listen before accepting cuts or audio processing.
- [Auphonic](https://auphonic.com/pricing): optional difficult-audio processing. Its free two hours/month includes a jingle; do not silently add that to deliverables.
- [Eden AI](https://www.edenai.co/feature/video-generation) and [Eden.art](https://eden.art/) are different services. Resolve which is intended. Eden AI lists a [5.5% credit-purchase platform fee](https://www.edenai.co/reduce-token-costs). Neither is a prerequisite or assumed saving.

For dated arithmetic, assumptions and the acceptance benchmark, see the repository's `research/services-and-costs.md`. If only this skill folder is installed, the workflow above remains self-contained.
