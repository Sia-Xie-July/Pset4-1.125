# Before the Merge: Source Entry Points, Independence and Verification Limits

Configured sources are in `config/sources.json`. These notes explain why each entry point was
chosen, how independence is counted, and what changed during the run week. Every run keeps its
own configuration snapshot under `runs/RUN_ID/config/`, so a later change here never rewrites an
earlier run.

## Current configuration (after the 2026-10-15 clean-up)

9 entry points in 7 conservative publisher groups, covering all three input types.

| Type | Source | Publisher group | Notes |
|---|---|---|---|
| Feed | Simon Willison, original entries — https://simonwillison.net/atom/entries/ | simon-willison | First-person practice and tool experiments. Entries (not "Everything") to avoid link posts and quotes. Not evidence of general team efficiency. All of this author's endpoints count as one publisher. |
| Feed | GitHub Copilot changelog — https://github.blog/changelog/label/copilot/feed/ | microsoft-github | Shows what the vendor offers; does not independently prove productivity, safety or savings. GitHub and Microsoft are merged into one group. |
| Feed | Cloudflare AI blog — https://blog.cloudflare.com/tag/ai/rss/ | cloudflare | Infrastructure vendor reporting on itself; accept only when it bears on small-team workflow. |
| Feed | METR — https://metr.org/feed.xml | metr | Research methods and proposals; method, proposal and measured result must be kept apart. Check that recent posts apply to this question rather than padding the month with old research. |
| YouTube | Amp, Inc. — *How Thorsten Ball Uses Amp, October 2026* (`Z7l1EHfCMU8`, ~34:31) | amp-inc | Vendor staff demonstrating a workflow; interest must be disclosed. A secondary directory listed a different date; the pipeline uses the native upload timestamp. |
| YouTube | Salvatore Sanfilippo (antirez) — `QobBTNIIX04` (~11:38) and `9h-Way-APlM` (~23:28) | salvatore-sanfilippo | Two distinct recordings, one independent publisher. Italian speech: English articles paraphrase and label it; the original timed segments are kept and no English quotation is invented. |
| YouTube | AIMUG talk by Jake Cukjati, *The coding factory: canonical specs and sequential agents* (`-65TrkDP1jY`, uploaded 2026-10-09, 1258 s; recorded 2026-10-05 per organiser) | aimug-jake-cukjati-nomi-health | Replaced the generic Modern SDE tutorial. 4:16–5:18 covers integration tests, review and token/context checks. First-person practice: long run times, code volume or the speaker's safety judgment are not treated as measured gains. |
| Podcast | HTML All The Things — https://podcast.htmlallthethings.com/feed.xml, one native episode: *Is AI Coding Making Technical Debt Worse?* (2026-09-19, 1226 s) | html-all-the-things | Hosts' experience and opinion on delivery pressure and technical debt, not a controlled study. The site discloses CodeRabbit sponsorship and Scrimba affiliate commission. |

Entry-point counts are not the same as the required 12 eligible substantive items from 6
independent sources; that is checked on the collected items of each run.

**Podcast coverage caveat.** This configuration names only one podcast episode. The evidence
store still contains earlier eligible podcast items (The AI Daily Brief and HTML All The
Things) that are re-filtered against each run's date, so the live run met the two-podcast
minimum from the store. A run started from an empty store would need one more working episode.

## How independence and credibility are judged

- Publisher count is not experiment count. One vendor result repeated by several authors is
  one underlying claim, not repeated verification.
- A podcast and its YouTube upload are one item; mirrors and different shows from the same
  producer do not add independence.
- Credibility is judged per claim, not by organisation reputation or popularity.
- Hosts' analysis must be separated from vendor information they relay; sponsor reads are not
  evidence (policy v2).

## Deliberate collection limits

- `max_entries` caps how many entries are inspected per source. When an archive is larger, the
  run records `limited` and `discovery_limit`. This gives every source a chance to be searched
  instead of letting one large archive use up the global `MAX_ITEMS`. Because the limit is
  intentional, the summary keeps `coverage_incomplete` explicit; the run never claims complete
  monitoring of every source.
- The default 20-minute media safeguard rejects some configured recordings. The operator raises
  it deliberately (`MAX_DURATION_MINUTES=40`, later 65–70 for hour-long episodes); this does not
  guarantee future episodes fit. If no native transcript exists, the pipeline falls back to
  local CPU faster-whisper. Errors are never ignored, and overlong episodes are never silently
  cut into an undisclosed excerpt to make up numbers.

## Sources considered but not used

- **Changelog News** (https://changelog.com/news/feed): readable, but the newest visible entry
  was 2026-04-29, outside the 30-day window.
- **Martin Fowler** (https://martinfowler.com/feed.atom): readable, but probed entries have no
  `published` field; the code does not treat `updated` as a first-publication date.
- **Syntax**: relevant recent episodes, but the RSS probe failed to decode/parse and the
  episodes far exceed 20 minutes. Not added rather than faked.
- **The AI Native Dev**: relevant interviews, but both Buzzsprout RSS addresses returned
  HTTP 403.
- **Superlinear** (`https://feeds.buzzsprout.com/2632181.rss`, episodes `Buzzsprout-19897974`
  and `Buzzsprout-19857951`): added on 2026-10-15, then removed because the audio kept
  returning HTTP errors.
- **The Modern SDE** (`zEl-wKCBrmQ`): original tutorial without a comparison baseline;
  replaced by the AIMUG talk. Items already collected from it stay in the store.
- **Research lead not collected:** the 2026-10-05 paper *Does Working with AI Agents Change How
  Developers Code, Test, and Review?*
  (https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.67). Worth verifying
  in full later; a web search result was not passed off as an RSS-collected item.

## Coverage gaps that remain

The candidate pool leans towards vendors and enthusiastic practitioners. Under-represented:
long-term maintenance and failure reports from real small teams, controlled comparisons,
non-English contexts and long-run cost. The editorial policy requires these gaps to be stated
rather than filled with manufactured counter-arguments or invented data.

## History of source changes

**2026-10-14 — metadata research.** All entry points above were probed (HTTP status, feed
parsing, yt-dlp metadata, caption availability). These probes downloaded and transcribed no
media, called no paid model, and were not a pipeline run. The original list also included
**The AI Daily Brief** (Nathaniel Whittemore, https://anchor.fm/s/f7cac464/podcast/rss): a
real feed with audio enclosures and more than 1,100 episodes, so `max_entries` was set; recent
episodes ran 28–40 minutes, above the default safeguard.

**2026-10-15 — first real collections.** `runs/20261015T033503Z-f6539b3bc938/` retained 22
eligible items. The recovery collection in `runs/20261015T035002Z-e05bbed2241b/` retained 25,
together with real receipts for a GitHub RSS failure, a YouTube extraction failure and their
recovery.

**2026-10-15 — podcast change.** In the second model selection, all three AI Daily Brief
episodes were rejected as generic AI news and promotion without specific coding-agent workflow
evidence, although the first selection had accepted them. This exposed instability in
relevance judgment; the rejections were not overwritten to satisfy coverage. (The human review
later disagreed with one rejection — see EDITORIAL_REVIEW.md, item R1.) The podcast source was
switched to HTML All The Things with two verified episodes: *AI Basics For Developers*
(2026-10-13, 3581 s, recorded 2026-09-30) and the technical-debt episode above. Both share one
publisher group. A 65-minute safeguard was used to process the hour-long episode.

**2026-10-15 — source discovery check.** `runs/20261015T044923Z-8de27f7e5e00/` is a live
discovery check only (`scope: source_discovery_validation_only`), not a full pipeline run.
`podcast-discovery.jsonl` is the first, partly failed result; `podcast-discovery-retry.jsonl`
is the result after fixing the request header (Buzzsprout returned 403 to the default Python
User-Agent and accepted a header identifying IntelligencePipeline). Both receipts are kept. It
can be replayed under that run's configuration snapshot:

```bash
PATH="$PWD/.venv/bin:$PATH" bash collectors/fetch_podcasts.sh runs/20261015T044923Z-8de27f7e5e00 --max-duration-minutes 70
```

**2026-10-15 — clean-up.** Superlinear was removed after persistent HTTP errors, *AI Basics For
Developers* was dropped after its rejection, and the AIMUG talk replaced The Modern SDE. Earlier
snapshots, failure receipts and stored evidence were kept; a run already in progress keeps
using its own snapshot. No accept decision was pre-written, and neither the policy nor the
prompts were loosened to admit sources.
