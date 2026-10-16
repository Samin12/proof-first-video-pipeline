# Proof, tweets, and generated media

## Build a small evidence ledger

For each checkable claim record:

```json
{
  "id": "claim-03",
  "scene_id": "scene-id",
  "timeline_ms": [12000, 18500],
  "spoken_claim": "Exact short claim needing support",
  "source_url": "https://example.org/original",
  "source_author": "Original publisher",
  "published_at": null,
  "captured_at": "2026-10-16T12:00:00Z",
  "support": "supported | partial | unsupported | unavailable",
  "evidence_path": "proof/claim-03.png",
  "evidence_sha256": "computed, not invented",
  "rights_note": "Creator's capture / licensed asset / review needed",
  "on_screen": "crop and highlight the relevant statement",
  "review": "pending"
}
```

Verify arithmetic from the source values using code. Distinguish an example calculation from an earnings claim, an announcement from a released feature, and a product demo from a promise. Conflicting evidence and claims stronger than the source go into a timestamped correction list for the creator.

## Research ladder

1. Reuse the project's existing source ledger and capture. Confirm its hash and freshness requirements.
2. Open the original page with the current harness browser. In T3 Code prefer its collaborative preview tools when present; elsewhere use the harness's supported browser. Capture only the relevant content at readable resolution.
3. Use targeted web/X search for missing sources. One query per distinct claim cluster; deduplicate URLs before fetching.
4. Use Firecrawl for pages whose extraction/capture is otherwise impractical or for a bounded batch. Avoid crawling a whole site to prove one statement. Its cache still bills credits; your local cache avoids a new request.

For tweets/X posts, preserve the canonical post URL, author/handle, exact wording, date, and any context necessary to understand it. Verify the actual post, not just the search summary or Grok's answer. If the original is inaccessible, label the evidence unavailable or secondary and tell the creator; do not generate a convincing fake screenshot. Edited/removed posts can make an old screenshot historically valid but unsuitable as a statement about the present.

Keep the untouched capture and a derived crop/highlight. A branded card may quote verified text with attribution, but must not pretend to be an untouched platform screenshot. Preserve original values; redactions should be visibly redactions. Inspect final pixels for author, quoted wording, numbers, and readability. Do not publicly commit browsing sessions, cookies, private dashboards, transcripts, or account screenshots with the skill.

## Media service adapter contract

Prefer the tools actually available in the harness. A provider is optional until the job needs it. Record `provider`, `billing_route`, `model`, `input hashes`, `prompt hash`, `job_id`, `status`, `asset path/hash`, and `actual cost` when supplied. Keep credentials in the provider's normal auth storage or environment, never a manifest.

For Higgsfield: inspect its current model catalog/constraints and account route; get a cost estimate; submit only within the authorized spend. Some quote tools import HTTPS reference media: omit media for a price-only quote, or reuse already confirmed media IDs and respect upload authorization. An estimate is not validation or a completed video. Reuse the returned prepared parameters/job ID, wait with backoff, download the completed result, verify duration/aspect/content, then import it via the Borumi writer. Do not resubmit a timed-out request before checking its job status. A reroll is a new paid attempt.

Use generated media for illustrations, transitions, or explicitly synthetic demonstrations. Do not use it as a tweet, screenshot of a product's real state, customer testimonial, or evidence of a factual claim. For most tutorials a source capture plus a deterministic crop/highlight is cheaper and clearer. Use short previews to choose the shot, then render only selected shots at final quality.

Eden is an optional adapter, not a mandatory purchase or assumed account. Confirm which Eden product the user means and its actual tool/API/billing capability before a paid job. The same job contract applies. If unavailable, keep the source/research work moving and deliver a local still/card placeholder with its pending status.

Read [services and billing](services.md) for current documented capabilities and dated pricing. A connected MCP in one harness is not automatically connected in another; discover and configure the required provider there using its official method.
