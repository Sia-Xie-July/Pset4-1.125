# Policy v1 vs v2 — selection stage only

Same run, same 28 eligible items, same prompts and model; only the policy snapshot differs.

- v1: accept 25, reject 2, defer 1; piece assignments 01=15 02=21 03=9
- v2: accept 23, reject 1, defer 4; piece assignments 01=20 02=20 03=15

| Review ID | Item | v1 | v2 | v2 reason (start) |
|---|---|---|---|---|
|  | Introducing Clef-omni with full multimodality, plus a faster | accept 01,02,03 | accept 01,02 | The passage discusses Cloudflare's development of Clef-omni, a model that processes multimodal data efficiently by skipping output token generation. This is rel |
|  | Enterprise managed settings enforcement updates | accept 02 | reject  | The content discusses GitHub Copilot client settings and enforcement updates, which are not directly related to AI coding agents' capabilities, workflows, or de |
| A3 | Gemini 4 Argon in GitHub Copilot | accept 01,02,03 | accept 01,02,03 | The passage reports that Gemini 4 Argon, a new model in GitHub Copilot, solved more tasks than previous Gemini models on every coding benchmark, with significan |
|  | HydraFusion updates and new Max option | accept 01,02,03 | accept 01,02 | The passage describes specific updates to HydraFusion and HydraFusion Max, including changes in model selection, reasoning effort allocation, and task-specific  |
|  | AI systems could cover up misbehavior | accept 02 | accept 02,03 | The passage discusses a vulnerability in the Inspect framework that could allow AI agents to modify transcripts during evaluations, which is relevant to the cen |
|  | How an assessor could investigate evidence of acceleration f | accept 02 | accept 01,02 | The passage provides specific guidance on what evidence is required to assess the reliability of claims about AI coding agents' impact on delivery workflows. It |
|  | How an assessor could investigate alignment of unreleased AI | accept 02 | defer  | The passage discusses alignment assessment of AI models but does not provide evidence of changes in coding-agent workflows, efficiency claims, or evaluation cri |
|  | A proposal for better informing the public about loss-of-con | accept 02 | defer  | The candidate provides a proposal for improving public evidence about loss-of-control risks from frontier AI development, but it does not directly address AI co |
|  | Our approach to working with AI companies | accept 01,02,03 | accept 03 | The passage discusses METR's approach to gathering and publishing evidence about AI loss-of-control risks, which is relevant to the central question about what  |
| A1 | Hello Python 3.15, goodbye 3.10, and now I can use 3.11 | accept 01 | accept 01,02,03 | The passage discusses Python 3.15's release, including features like unpacking in comprehensions and improvements to profiling tools. These developments are rel |
|  | We're going to need default hard budget caps on pretty much  | accept 02 | accept 01,03 | The passage discusses the importance of default hard budget caps for pay-by-usage services and APIs, which is relevant to the editorial question about changes i |
|  | Claude Haiku 5.5 | accept 02 | accept 01,02 | The passage provides specific cost and time metrics for Claude Haiku 5.5, which is relevant to the central question about task-level time and token costs. It de |
| A2 | A new feature for my blog, built using my voice | accept 01,02,03 | accept 01,02 | The passage describes a practical use case of a coding agent, where the author used voice interaction to build a feature, reviewed the code, and made adjustment |
|  | OpenAI DevDay 2026 live blog | accept 01,02,03 | accept 01,02 | The passage discusses how coding agents are harder to get going with than ChatGPT, and how unifying Codex and ChatGPT helped more people become builders. This i |
|  | AI Basics For Developers | accept 01,02 | accept 01,02,03 | The podcast passage discusses the evolving nature of AI coding tools and introduces the concept of a 'harness' that manages permissions, tool context, and verif |
|  | Is AI Coding Making Technical Debt Worse? | accept 01 | accept 01,02,03 | The podcast discusses the impact of AI coding on technical debt, specifically highlighting how reliance on AI can lead to unvetted code and maintainability issu |
|  | How to Go from AI Power User to AI Leader | accept 02 | defer  | The passage lacks specific evidence about changes in coding-agent workflows, efficiency claims, or evaluation criteria relevant to small teams. It discusses AI  |
| R1 | What Gemini 4 Argon Is Actually Good For | reject  | accept 01,02,03 | The passage discusses how Blitzie's agents modernize legacy systems by reverse engineering them into a persistent knowledge graph and autonomously executing mig |
| R2 | Why Muse Wonder Is Dividing AI Users | reject  | accept 01,02 | The podcast provides specific insights into the performance and capabilities of Meta's Muse Wonder models, including benchmark comparisons and user experiences. |
|  | The coding factory: canonical specs and sequential agents |  | accept 01,02 | accept 01,02,03 | The passage describes a practical workflow for using AI coding agents in a small team setting, with specific details on task specification, agent implementation |
|  | Il mio approccio alla programmazione automatica | accept 01 | accept 01,02,03 | The passage discusses the practical use of coding agents in a design and verification process, highlighting the need for a process of design, code writing, veri |
| D1 | Stare nel flow: qualche aggiornamento sulla mia esperienza | defer  | defer  | The excerpts do not show relevance to AI coding agents, task specification, testing, review, delivery outcomes, permissions, or cost. The content discusses pers |
|  | How Thorsten Ball Uses Amp, October 2026 | accept 02 | accept 01,02,03 | The passage discusses changes in coding-agent workflows, including reduced development time, faster debugging, and the ability to build new functionalities. It  |
|  | Types of AI Agents in 2026 and Choosing a Model | Building A | accept 01 | accept 01,03 | The passage discusses coding agents, their role in reading repositories, editing files, and running tests, which directly informs piece 01 (What changed in codi |
