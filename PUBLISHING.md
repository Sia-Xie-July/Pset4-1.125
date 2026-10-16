# Review and production handoff

Activate `.venv`, then run `bash run.sh`. Configuration and prompts must contain
your own editorial decisions. The default run coordinates both workflows, checks
content, and saves summary.json last, including on failure. `--collection-only`
stops after collection for diagnostics; it does not complete the publication pipeline.

Each component is independently runnable:

```bash
R=runs/RUN_ID
bash review/check_content.sh "$R" > "$R/review.json"
# Inspect the actual articles, scripts, briefs, source passages and review issues.
# Only you supply approval.json; the pipeline never creates your human decision.
bash publishing/prepare_package.sh "$R"
bash reporting/summarize_run.sh "$R" > "$R/summary.json"
```

approval.json requires the current review_id, decision (`approve` or `revise`),
nonempty reviewer, ISO 8601 UTC reviewed_at, and string notes. The example in
examples/approval.json illustrates the shape only. Do not copy its fictional
decision as your real review. Mechanical checks cannot establish sound interpretation,
publisher independence, or article/script semantic consistency.

After your approval, use `bash run.sh --package "$R"`. This reruns checks,
packages only on matching approval, and refreshes summary.json. It never collects,
regenerates drafts, or changes original config/prompt snapshots. Direct packaging
also recomputes a full assessment. Missing, nonapproving or stale approval exits 1.
Changing any draft, brief, manifest, decision, evidence reference, retained evidence
asset or run metadata changes the SHA-256 review fingerprint (which explicitly
includes as_of_date). Logs, approval and package outputs are excluded. Review
assessment exits 0 even when passed is false; inspect passed and issues.

The package contains articles/01–03.md, video_scripts/01–03.md,
source_notes/01–03.md, manifest.json with piece IDs, paths and SHA-256 hashes,
MANUAL_STEPS.md, and publication_links.json. Repackaging archives the previous
package under attempts/ and preserves publication_links.json bytes, including
entered URLs. Malformed link records exit 2 without replacing the package.

Render and inspect each video in Google Vids or HeyGen. Publish shareable Substack
articles and public or unlisted YouTube videos, link each pair both ways and include
source references. Enter actual URLs in package/publication_links.json, then verify
staff access. A prepared package means ready_for_production; it does not establish
that videos are rendered or content is published. Summary links are reported
separately and publication_verified stays false pending human verification.

Summary statuses are failed, awaiting_review, ready_for_production. Counts are null
when unmeasured and zero for measured empty files; coverage uses distinct item_id
values and reports duplicate raw observations separately. Collection failures and
limits remain explicit. Costs are the known subtotal of retained receipts (running
and final lifecycle receipts are deduplicated); unknown costs and estimates remain
explicit. Fixture model cost 0 is a measured absence of API calls, not an inferred
zero for unpriced live work.

Offline tests use isolated, clearly fictional evidence and simulated approvals:

```bash
python3 -m pytest -q tests/test_publishing.py tests/test_editorial.py
python3 tests/dry_run_publishing.py
```
