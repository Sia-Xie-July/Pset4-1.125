# Before the Merge: Topic and Editorial Brief

This is the project's real topic configuration. It is not fictional evidence and not a record
of completed publication. Articles, video scripts and all project documentation are in English.

## Topic, audience and question

- **Publication name:** Before the Merge.
- **Topic:** How small software teams can adopt AI coding agents on the basis of evidence,
  focusing on delivery speed, verification effort, quality, permissions and cost.
- **Single primary audience:** Technical leads of 3–10-person software teams building web
  applications or internal tools. They understand Git, pull requests, tests and CI, but have
  no dedicated AI evaluation team.
- **Central question:** Which developments from the past 30 days justify changing a team's
  workflow, and what evidence is needed before giving agents more autonomy?
- **Voice:** English; specific, restrained, with checkable judgments. A vendor feature
  description is not independent evidence of efficiency, and a personal account is not a
  general causal conclusion.
- **Why readers return:** Each edition tracks new material, changes to earlier material and
  whether earlier views need revision, and gives decision criteria a small team can test.

## Editorial direction of the three-part series

These were working titles and questions, not conclusions fixed in advance; the formal briefs
had to be generated from real accepted evidence.

1. **More Agent Output, Better Delivery? What Changed This Month**
   Which specific delivery step does a new capability change? What is still only a demo or a
   vendor claim?
2. **The Review Bottleneck: Which Productivity Claims Survive Scrutiny?**
   Against real tasks, baselines, review and rework cost, explain which efficiency claims hold
   and which remain uncertain. If the evidence did not support a "review bottleneck", the title
   and argument had to change.
3. **Before You Expand Autonomy: A Small-Team Evaluation Plan**
   Derive a reversible trial plan from the evidence in pieces 1 and 2, separating proposed
   metrics from measured results; never claim that we ran a team experiment.

Each piece needs at least three independent sources, its own argument, cross-source synthesis
and stated limitations. Across the series, written articles, YouTube and podcasts must all
contribute substantive evidence. Articles are about 600–900 English words; videos about 3–5
minutes.

## Limits of source research

Source entry points and initial independence judgments are in SOURCE_NOTES.md. HTTP
reachability, search-result dates, research notes and script output are different levels of
evidence and do not substitute for one another. Only items that the pipeline actually
collected, retained as full text or transcript, stored as a version and passed through the
date filter can support a formal claim.

The code blocks invalid dates and obvious duplicate recordings, but publisher ownership,
sponsorship, context and whether an argument is truly supported still require human review.
The source configuration is not proof that the 12-item / 6-independent-source minimum is met.

## What the two live runs compare

Run at least twice on different UTC dates during the assignment week. This does not mean
waiting 48 hours, and it does not require three new pieces each day. The second run reuses the
same store and compares new / changed / unchanged items, date exclusions, source failures and
editorial choices, and explains whether those changes alter any article's argument or
limitations. If no meaningful new material appears, record that honestly and add a clearly
labelled replay demonstration. Do not change the system date or a run's `as_of_date`, and do
not present a same-day replay as a second day's live run.

After human review, the editorial policy is revised at least once, preserving the old and new
policy, the affected stage outputs and the comparison. Status: the review is recorded in
EDITORIAL_REVIEW.md; `config/editorial_policy.md` is now v2 (v1 is kept at
`docs/policy/editorial_policy_v1.md`); the rerun is in
`runs/20261015T052758Z-daba50c83a0b/policy_v2_rerun/`.

## What only exists after real execution

Model decisions, articles, scripts, human review, second-date changes, publication links and
the demonstration video are filled in only after they actually happen; none are pre-written.
Operating steps are in NEXT_STEPS.md; the human review record is EDITORIAL_REVIEW.md.
