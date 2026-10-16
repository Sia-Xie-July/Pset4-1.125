# Corrected brief fields and article bodies (human-requested corrections, 2026-10-15).
BRIEFS = {
"01": dict(
 question="What changed in the preceding 30 days in how practitioners organise coding-agent work, and which of those changes matter to a small team?",
 argument="This month's practitioner accounts show agent work being organised into more explicit structures — specifications, staged plans, iterative check-ins and clearer job definitions — but they demonstrate a process, not a measured improvement in delivery quality or a reduction in human verification.",
 synthesis="Cukjati describes a specification-to-implementation workflow in which agents test and implement the work (01-c1). Sanfilippo describes agent use as an iterative loop of design, code, verification and small changes rather than one perfect prompt (01-c2, paraphrase of automatic English captions). The Modern SDE groups agents by what they do (01-c3). Our inference (01-c4) connects these: the common development is a move from prompting to an inspectable process with a defined job, and that structure is what a team can evaluate. None of the three sources measures review time, defects or delivery speed, so the structure is a hypothesis to test, not a demonstrated gain.",
 limitations="All three sources are self-reported practitioner or teaching accounts without baselines or measurements. The Sanfilippo evidence is machine-translated captions, used only as paraphrase. Missing perspectives: teams for whom structured agent workflows failed, long-term maintenance cost, and controlled comparisons.",
 claims={
  "01-c1": ("source_claim", "Jake Cukjati describes a workflow in which agents take a specification into implementation planning and then test and implement the work."),
  "01-c2": ("source_claim", "Salvatore Sanfilippo describes productive agent use as an iterative process of design, code writing, verification and small changes rather than writing one right prompt (paraphrase of automatic English captions of Italian speech)."),
  "01-c3": ("source_claim", "The Modern SDE groups AI agents by what they do rather than adopting a borrowed list of agent types."),
  "01-c4": ("inference", "Read together, these accounts point to a shift from prompting to a structured, inspectable process with a defined job for the agent; they do not show that the structure improves delivery quality or reduces human verification, which would require a measured comparison."),
 }),
"02": dict(
 question="Which claims about coding agents verifying their own work withstand scrutiny, and where is the evidence weaker than the claim?",
 argument="This month's claims that agents can verify their own work arrive as three different kinds of evidence — practitioner framing, a sponsor's performance claim and a workflow description — and none independently measures a reduction in review burden, so a team should ask where verification work moves rather than whether an agent runs a check.",
 synthesis="The HTML All The Things hosts frame the hard part as keeping control of the codebase (02-c1). An advertisement read in The AI Daily Brief claims over 80% of software epics delivered autonomously (02-c2). Cukjati describes one-agent-at-a-time work with a test harness for integration and end-to-end checks (02-c3). Our inference (02-c4): these are not three confirmations of one productivity result; each is a different kind of evidence, and none measures review time, rework or later defects. Verification work may be moving to specification, test interpretation and correction rather than disappearing.",
 limitations="Selected excerpts, not an empirical survey. The 80% figure is a sponsor claim with unknown denominator and method. Missing measurements in these excerpts do not show that agents are ineffective. The title's 'review bottleneck' framing is a question posed by this piece, not a finding established by the sources.",
 claims={
  "02-c1": ("source_claim", "The HTML All The Things hosts say the hard part of AI coding tools is not choosing the smartest model but learning to work with them without giving up control of the codebase."),
  "02-c2": ("source_claim", "An advertisement for Blitzy read during The AI Daily Brief claims the product delivers over 80% of entire software epics autonomously, validated and end-to-end tested; this is a sponsor claim, not a verified result."),
  "02-c3": ("source_claim", "Jake Cukjati describes working with one agent at a time and using a test-harness plugin so that agents check completed specs with integration and end-to-end tests."),
  "02-c4": ("inference", "These passages are different kinds of evidence, not three confirmations of one productivity result; none measures review time, rework or post-release defects, so the verification burden may be moving to specification and correction rather than disappearing."),
 }),
"03": dict(
 question="What do this month's developments imply for a small team deciding whether to give coding agents more autonomy, and what should it measure next?",
 argument="New agent options keep arriving, but none of this month's retained sources measures a small team's delivery outcomes, so the defensible next step is a bounded, reversible evaluation of the team's own work before any expansion of agent autonomy.",
 synthesis="GitHub documents that Gemini 4 Argon is available to specified Copilot plans (03-c1): an available option, not an outcome. Cloudflare reports that automated traffic surpassed human activity and describes the influence of agent-driven recommendations (03-c2): an ecosystem narrative from a vendor. METR states its goal of accurate, timely, independent evidence and notes that many relevant claims remain open questions (03-c3): an evaluation principle from a different domain. Our inference (03-c4) turns these three distinctions into a decision process for a team: choose a bounded task, fix a comparison in advance, count the whole human effort, and set expansion and stop criteria before looking at results.",
 limitations="The evaluation plan is our proposal, not an experiment we conducted. METR's subject is frontier-lab risk assessment, not software teams; only its evidence principle is borrowed. GitHub and Cloudflare are vendors describing their own ecosystem. Small samples, task differences and evaluator judgment will limit any single team's pilot.",
 claims={
  "03-c1": ("reported_fact", "GitHub states that Gemini 4 Argon is available to Copilot Pro+, Max, Business and Enterprise users and can be selected in the model picker."),
  "03-c2": ("source_claim", "Cloudflare reports that automated traffic surpassed human activity and describes the influence of agent-driven recommendations on consumer choices."),
  "03-c3": ("source_claim", "METR states that its goal is accurate, timely and independent evidence about AI loss-of-control risk, gathered by collecting concrete evidence and publishing it, while many relevant claims remain open scientific questions."),
  "03-c4": ("inference", "Together these sources separate an available capability, a vendor's ecosystem narrative and an evaluation principle; since none measures a small team's delivery, expanding autonomy should follow a bounded, reversible evaluation of the team's own work."),
 }),
}
# 03: re-map evidence so each statement cites the passage it describes (original mapping was rotated).
EVIDENCE_REMAP_03 = {"03-c1": "github.blog", "03-c2": "blog.cloudflare.com", "03-c3": "metr.org"}
