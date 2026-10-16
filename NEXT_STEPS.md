# Local Pipeline Operating Guide

## Start

No API key is needed, and any old `.env` is not read. If Ollama is not running, start it in a
separate terminal:

```bash
OLLAMA_NO_CLOUD=1 ollama serve
```

From the repository root run `bash run_local.sh`. The model is the already-downloaded
`qwen3:8b`. Only source collection needs internet access; model inference runs on this machine.
Keep the `RUN_DIR` printed by the terminal. The automated end point is `awaiting_review`, not
"published".

`run_local.sh` only sets the local environment (local Ollama model, faster-whisper settings,
`MAX_DURATION_MINUTES=70`) and then calls `run.sh`, which owns orchestration and receipts.

If generation is interrupted after selection, run
`bash run_local.sh --resume-series runs/RUN_ID`. It keeps that run's date, configuration and
selection decisions, retries from the briefs, moves earlier generated output to `attempts/`, and
never deletes historical receipts. Do not use it to pass off a resumed run as a new collection
run on another date.

## Small-context implementation and its limits

- Selection is one request per item: up to four passages ranked by topic keywords are
  retrieved from the original text, and the excerpt range is labelled explicitly.
- Briefs are one request per piece: a small set of original passages from three independent
  publishers; the model produces three source-based claims and one cross-source inference.
- Articles and scripts are one request per piece, sending only that brief and the passages it
  cites, not the whole evidence store.
- Passage IDs are mapped back in code to the real item / version / quote / segment, so the model
  never has to repeat long hashes.
- The model never sees the full context. Excerpt bias, quotes taken out of context and the
  strength of support for each claim still need human checking (see EDITORIAL_REVIEW.md, where
  this caused two of the disagreements).
- Original evidence and historical receipts are kept. Exceeding the local context fails
  explicitly; nothing is silently truncated.
- API cost is zero, excluding electricity and hardware.

## Course requirements that still apply

The 30-day window; at least 12 items from 6 publishers with at least two of each input type;
each piece cites at least three publishers; and all three input types contribute evidence to the
series. The corpus is the current configuration plus still-eligible historical evidence in the
store; a fresh environment cannot assume it already has the historical podcast material.

## Status of the student steps

1. ~~Check the three articles, three scripts, citations and `review.json`.~~ Done; corrections in
   `runs/20261015T052758Z-daba50c83a0b/human_edits/CORRECTIONS.md`.
2. ~~Review at least three accepts and three rejects/defers, revise the policy and rerun selection.~~
   Done: `EDITORIAL_REVIEW.md`, policy v2, `runs/20261015T052758Z-daba50c83a0b/policy_v2_rerun/`.
3. ~~Re-run the content check on the corrected drafts.~~ Done (`review.json`, `passed: true`).
4. ~~Write `approval.json` and package.~~ Done (`ready_for_production`, `package/`).
5. ~~Second live run on a different UTC date.~~ Done: `runs/20261016T000750Z-75c221157a38`;
   comparison in `docs/RUN_COMPARISON.md`.
6. ~~Produce and publish the videos and articles.~~ Done: three Google Vids videos on YouTube
   (unlisted) and three free Substack posts, linked both ways; URLs in
   `runs/20261015T052758Z-daba50c83a0b/package/publication_links.json`.
7. ~~Technical demonstration.~~ Done: `demo/Before_the_Merge_technical_demo.mp4`.
8. Push to your own GitHub repository, add its URL at the top of SUBMISSION.md, and open every
   link once in a private browser window.
