# Write the three Before the Merge articles

Return only the required {"documents":[Document,Document,Document]} object in
English, one document per piece 01/02/03. Follow the supplied schema, project,
snapshotted policy, briefs and exact retained evidence. No Markdown code fences
around the JSON. The markdown field contains the audience-facing article.

Write approximately 600–900 English words per article excluding source notes.
Speak to a technical lead who knows Git, tests and CI but has no dedicated AI
evaluation team. Open with a concrete decision or tension; develop the brief's
distinct argument with a cross-source insight, a material limitation, and an
actionable implication. Avoid three summaries of the same product announcements.
Use a calm, specific voice; no invented scenes, quotations, interviews, statistics,
experiments, cost savings, or personal use of the tools.

The supplied brief is the factual contract. Copy its claims and evidence exactly
into the output claims field, preserve every claim_id in claim_ids, and place the
corresponding markers naturally in the article. Do not introduce substantive claims
outside that contract. Clearly attribute source_claim statements; label interpretation
and uncertainty. A proposed evaluation is a proposal, not a test we performed.

Only quote literal excerpts of the cited locator passages. Paraphrase without
quotation marks when appropriate. Do not use invented scare quotes or decorative
blockquotes: direct quotes are checked programmatically. Never alter a locator,
claim type, statement or exact version. The component appends canonical source
notes and the run's as-of date; do not fabricate competing sources, publication
URLs, dates or video links. Include a brief disclosure of AI assistance and required
human review without implying approval has already occurred.
