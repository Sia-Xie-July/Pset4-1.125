# Before the Merge — Editorial policy v2

Revised 2026-10-15 after human review of run 20261015T052758Z-daba50c83a0b
(see EDITORIAL_REVIEW.md). v1 is preserved at docs/policy/editorial_policy_v1.md.

Write in English for technical leads of 3–10-person software teams shipping web
applications and internal tools. The recurring question is whether recent changes
in coding agents justify changing delivery practices, and what evidence should
precede greater autonomy. Neither adoption nor rejection is a predetermined answer.

## Relevance and novelty

Accept material that can change a concrete decision about task scoping, agent
context, tests, review, permissions, rollback, delivery quality, or cost. State what
is newly reported, demonstrated, measured, or learned. A new model or feature is
not sufficient without a plausible connection to this audience's work. Reject
generic AI commentary, investment speculation, and unrelated tool news. Defer a
relevant item when a specific missing passage, date, method, or disclosure can be
obtained. Relevance and credibility are separate judgments.

Relevance must be shown by a specific passage, not asserted. An accept reason must
name the passage and the decision it informs (for example: review time, default
permissions, per-task cost). Programming-language or runtime releases, general model
launches, and frontier-lab governance or safety-policy proposals are rejected unless a
passage connects them to how a small team uses, checks, permits, or pays for a coding
agent. A credible publisher does not make an off-topic post relevant. A reason that
says the item "does not directly address AI coding agents" cannot end in accept.

## Freshness and original identity

Only use the eligible evidence supplied by the run. Its inclusive UTC window is
as_of_date minus 29 days through as_of_date. Never invent a publication timestamp
or replace it with retrieval time. Reuploads, refreshed dates, removal of a
paywall, and syndicated copies do not make old work newly published. Distinguish
the date of a recent report from the date of the experiment, event, or software
version it discusses. Older studies may suggest questions for research planning,
but must not supply substantive publication claims under this assignment's window.

Count the same recording once across YouTube and podcast routes; preserve the
canonical item's kind and its own timestamp offsets. Several outlets repeating
one announcement or experiment are not independent corroboration. Explain the
originating observation rather than treating publisher count as a vote.

## Claim-specific credibility and incentives

Prefer primary documentation of capabilities, original research with a stated
method, and first-person practitioner accounts with inspectable examples. Examine
what each passage actually supports; reputation, popularity, and confidence are
not proof. Separate four categories in reasoning: demonstrated capability,
self-reported experience, measured outcome, and our inference.

Vendor announcements establish what a vendor says or offers, not an independent
productivity or safety result. Disclose employment, ownership, sponsorship,
affiliate links, paid products, credits, and relevant consulting interests when
known. Unknown disclosures stay unknown. Benchmarks require their task setting,
baseline, model/tool version, outcome definition, and meaningful limitations.
Do not infer team throughput from generated code, commits, benchmark scores,
or an impressive single demonstration. Assess testing and review time alongside
generation time; causal language requires an appropriate comparison.

Classify capability adjectives without a stated task, baseline, or number ("solves more
tasks on every benchmark", "thoroughly checks its work") as unverified vendor claims.
When a vendor post also states operational facts — availability, billing, default
enablement, admin controls — prefer those as the decision-relevant content, and look
for practitioner reports that confirm or contradict the capability claim.

Sponsor reads and advertisements inside a podcast or video are never evidence of
outcomes; they may only be cited as an example of a marketing claim and labelled as
an advertisement. When a host relays other people's posts or benchmarks, attribute
each statement to the named original speaker, treat it as self-reported and
unverified, and do not count relayed speakers as independent corroboration.

## Perspective and independence

Seek vendor capability evidence, practitioner experience, and critical empirical
evaluation. Do not manufacture agreement or disagreement to fill these categories.
Group endpoints from the same originating producer with the same publisher_id.
GitHub and Microsoft are one corporate group for independence checks; Syntax
endpoints share their Sentry-affiliated producer group; an author's video and
podcast copy are one recording. Ownership grouping is conservative, not proof of
independent experimental evidence. Flag missing small-team experience, maintenance
costs, unsuccessful deployments, non-English contexts, and longer-term outcomes.

## Selection decisions

Emit exactly one accept/reject/defer decision for every supplied eligible item.
Give a specific reason grounded in its actual content, publication context,
relevance, incentives, or limitation. Accepted items name the intended piece IDs.
Rejected and deferred items have no piece assignment. Deferral must identify what
would resolve it. Never invent a source, quote, date, sample size, result, or
personal experiment to meet a quota. If the series lacks enough accepted evidence,
say so and stop rather than lowering standards silently.

Selection sees bounded excerpts, not whole sources. Judge the excerpts you were
given, and do not describe a source as incoherent, speculative, or irrelevant as a
whole on the basis of excerpts alone. If the title, description, or kind indicates
coding-agent content but the excerpts do not show it, choose defer and state which
topic or time range should be inspected. Reject only when the excerpts and metadata
together show the item is outside scope.

Assign only the pieces whose editorial question the passage actually serves, and say
why for each. Do not assign all three pieces by default: piece 01 needs evidence of
what changed, piece 02 needs claims and counter-evidence to test, and piece 03 needs
material that informs an evaluation or permission decision.

## Synthesis, uncertainty, and references

Each piece advances a distinct argument, uses at least three originating publishers,
connects multiple sources into an explicit insight, and addresses a real limitation
or counterargument. All three required input kinds contribute to the series.
Reuse evidence only when it serves a different analytical purpose.

Every claim is reported_fact, source_claim, or inference and has evidence at the
exact item_id/version_id. Written locators quote a literal retained passage;
audio/video locators name an existing segment_id with numeric timestamps.
Do not rewrite words inside a locator, translate an exact quote, or invent timing.
For non-English primary media, an English paraphrase must be identified as a
paraphrase; retain the original segment text and locator. A translation is not an
exact English quotation. Flag translation and auto-caption uncertainty for human review.
Automatic YouTube captions of non-English speech are machine translations even when
the transcript metadata reports English; use them only for paraphrase.
An inference must explain its reasoning in synthesis and must not outrun its
premises. Attribute observations and separate proposed practices from measured
results. Do not present a proposed team pilot as an experiment we conducted.

An item being accepted does not establish every statement in it as true. Prefer
qualified conclusions over universal prescriptions. Describe disagreements in
terms of tasks, methods, versions, incentives, and measurement differences.

## Publication, review, and corrections

Articles target 600–900 English words excluding sources. Scripts target 3–5 minutes
of spoken English and provide practical visual directions for Google Vids or
HeyGen. The two forms preserve the same supported claims, limitations, exact source
versions, and as-of date. Markers aid inspection; audience-facing source notes
and timestamp links are still required. Disclose AI assistance in publication.

Mechanical checks do not establish sound interpretation. The student must inspect
at least three accepted and three rejected/deferred items, compare the model's
reasons with their own judgment, record factual corrections with evidence, and
approve only the actual reviewed fingerprint. Revise this policy after that real
inspection, preserve both versions and outputs, and explain the effect.

## Changes from v1 (2026-10-15)

Each change answers a specific finding in EDITORIAL_REVIEW.md:

- Relevance must be shown by a named passage; off-topic posts from credible publishers
  are rejected (review item A1 Python 3.15).
- Vendor capability adjectives are classified as unverified claims; operational facts
  such as default enablement are preferred (A3 Gemini 4 Argon changelog).
- Sponsor reads are never outcome evidence; relayed third-party posts are attributed
  and self-reported (R1, and brief 02's Blitzy advertisement).
- Excerpt-limited judgments default to defer with a named range rather than reject,
  and reasons may not call a source incoherent from excerpts alone (R1, R2, D1).
- Piece assignment must be justified per piece (A2, A3 were assigned to all three).
- Automatic captions of non-English speech are paraphrase-only (D1).
