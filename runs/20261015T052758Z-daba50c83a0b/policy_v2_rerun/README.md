# Policy v2 selection rerun (labelled same-date stage replay)

Purpose: show the effect of the editorial-policy revision on the affected stage.
Only `editorial/select_items.sh` is rerun, on this run's own 28 eligible items, with the
same as_of_date (2026-10-15), prompts and local model. The only changed input is
`config/editorial_policy.md` (v2). This is NOT a second live run and does not collect anything.

- v1 policy: `editorial_policy_v1.md` (identical to the parent run's snapshot)
- v2 policy: `config/editorial_policy.md` (identical to the repo's current `config/editorial_policy.md`)
- Diff: `docs/policy/v1_to_v2.diff`
- v1 decisions: `decisions_v1.jsonl` (copied from the parent run)
- v2 decisions: `decisions_v2.jsonl` (written by the rerun)
- Comparison: `comparison.md` (written by `compare_decisions.py`)
- Receipts and raw model outputs: `logs/`, `model_outputs/`

Run on the Mac (Ollama must be running: `OLLAMA_NO_CLOUD=1 ollama serve`):

    bash runs/20261015T052758Z-daba50c83a0b/policy_v2_rerun/run_selection_v2.sh

Interpretation notes: the model is stochastic, so compare the reviewed items (A1–D1 in
EDITORIAL_REVIEW.md) as well as totals. Excerpt retrieval is unchanged, so R1/D1 can at
best move to defer under v2, not to accept, unless the excerpts happen to include the
relevant ranges. Record the observed result honestly, including "no change".
