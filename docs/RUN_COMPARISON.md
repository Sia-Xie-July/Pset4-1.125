# Live run 1 vs live run 2

| | Live run 1 | Live run 2 |
|---|---|---|
| Run | [`20261015T052758Z-daba50c83a0b`](../runs/20261015T052758Z-daba50c83a0b/) | [`20261016T000750Z-75c221157a38`](../runs/20261016T000750Z-75c221157a38/) |
| as_of_date (UTC) | 2026-10-15 | 2026-10-16 (`previous_run_id` = run 1) |
| 30-day window | 2026-09-16 – 2026-10-15 | 2026-09-17 – 2026-10-16 |
| Policy snapshot | v1 | v2 (after human review) |
| Model | local Ollama `qwen3:8b` | same |
| Collection status | completed, all collectors exit 0 | completed, all collectors exit 0 |
| Discovered / extracted | 23 / 23 | 23 / 23 |
| Store changes | new 0, changed 0, unchanged 23 | **new 3**, changed 0, unchanged 20 |
| Duplicate observations | 0 | 0 |
| Eligible (written / podcast / YouTube) | 28 (18 / 5 / 5) | 31 (21 / 5 / 5) |
| Exclusions | 0 | 0 |
| Decisions accept / reject / defer | 25 / 2 / 1 | 25 / 0 / 6 |
| Content checks | passed | passed (4 warnings) |
| Status | approved and packaged; published | `awaiting_review` (not packaged or published) |
| Elapsed (collection → checks) | ~23 min | 912 s (~15 min) |
| API cost | $0 | $0 |

Run 2 reused the same evidence store (`data/store.sh`), so its `changes.jsonl` is computed
against everything already stored.

## What was new

Three written items published on 15 October, after run 1 had collected:

| Item | Publisher | Published | Run 2 decision |
|---|---|---|---|
| Agentic autofix for code scanning alerts general availability | GitHub changelog | 2026-10-15 13:49Z | accept → pieces 01, 02 |
| Upcoming deprecation of selected GitHub Copilot models in mid-November | GitHub changelog | 2026-10-15 19:35Z | accept → pieces 01, 03 |
| Cloudflare and OpenAI: Making AI discovery better for everyone | Cloudflare blog | 2026-10-15 13:00Z | defer (not about coding agents) |

No item changed version and no item was re-stored twice: the 20 previously seen items that
were re-discovered were recognised by identity and content hash and recorded as `unchanged`
without re-extraction. The other stored items (for example the AI Daily Brief podcast episodes,
no longer in the source configuration) stayed eligible from the store.

## 30-day window

Moving the as-of date by one day moved the window from 16 Sep to 17 Sep. The oldest eligible
item in either run is 19 Sep 2026 (HTML All The Things, technical debt), so no item crossed the
boundary and `exclusions.jsonl` is empty in both runs. The filter rule is unchanged
(`processing/filter_items.sh`, reason `outside_window` when an item precedes the window).

## Editorial changes

**Selection (policy v2 + new material).** Two v1 rejects became accepts (R1 Gemini 4 Argon podcast,
R2 Muse Wonder podcast); four v1 accepts became defers (GitHub enterprise settings, two METR
risk-assessment posts, one AI Daily Brief episode); the two new GitHub items were accepted and the
new Cloudflare item deferred. This matches the policy-only rerun
(`runs/20261015T052758Z-daba50c83a0b/policy_v2_rerun/`): v2 defers more and rejects less, but on
the human-reviewed items it does not reliably move towards the human judgment.

**Briefs.** The briefs drew on different evidence even though most of the corpus was unchanged:

| Piece | Run 1 evidence | Run 2 evidence |
|---|---|---|
| 01 | AIMUG talk, antirez video, Modern SDE lecture (all YouTube) | GitHub Argon changelog, Cloudflare Birthday Week, METR "AI systems could cover up misbehavior" (all written) |
| 02 | HTML All The Things, AI Daily Brief, AIMUG talk | AIMUG talk, antirez video, Amp (Thorsten Ball) video |
| 03 | GitHub, Cloudflare, METR | HTML All The Things, AI Daily Brief (Argon episode), AIMUG talk |

The two new GitHub items were accepted but not cited by any brief, so the new material did not
change any argument.

**Quality of the run 2 drafts (human check).** Run 2 repeats an error that the run 1 review
corrected: brief 01 presents GitHub's vendor statement that Gemini 4 Argon "solved more tasks than
previous models on every coding benchmark" and "thoroughly checks its work" as "a significant
change in agent capability", although policy v2 classifies such capability adjectives as
unverified vendor claims. Articles 02 and 03 are 522 words, below the 600–900 target (flagged as
warnings by `check_content.sh`). For these reasons run 2 was **not approved or published**; the
published series remains the reviewed and corrected output of run 1.

## What the comparison shows

- **Update detection works:** three genuinely new items were found, stored as new versions and
  passed through the date filter; unchanged items were not reprocessed or duplicated.
- **Editorial output is unstable:** with three new items out of 31, all three briefs were rebuilt
  around different sources, and a vendor claim corrected by human review reappeared. The cause is
  the same as in the review: selection and brief generation see only keyword-ranked excerpts, and
  a small local model does not apply the policy consistently. Human review before publication is
  therefore a required step, not a formality.
