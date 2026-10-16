# Technical demonstration — final narration and shot list

Video: [demo/Before_the_Merge_technical_demo.mp4](demo/Before_the_Merge_technical_demo.mp4) (4:48, 1920×1080, English captions burned in; soft subtitles in [demo/Before_the_Merge_technical_demo.en.srt](demo/Before_the_Merge_technical_demo.en.srt)).
Every screen shows commands and outputs from the real runs; the frames are rendered from `demo/source/content.py` by `demo/source/render.py` (synthesized narration, local TTS).

| # | Start | Requirement covered | On screen |
|---|---|---|---|
| 1 | 0:00 | Topic and audience | Before the Merge |
| 2 | 0:18 | Configuration (topic, sources, policy, prompts) | config/project.json  ·  config/sources.json |
| 3 | 0:40 | Architecture and entry point | Architecture diagram |
| 4 | 1:27 | Run 1 results and human approval | Run 1 · runs/20261015T052758Z-daba50c83a0b |
| 5 | 1:51 | Trace one source → decision → published claim | Tracing one published claim (piece 01, claim 01-c1) |
| 6 | 2:30 | Second run: new / unchanged / duplicates / 30-day window | Run 2 · runs/20261016T000750Z-75c221157a38  (as_of 2026-10-16) |
| 7 | 3:00 | Failure reporting and recovery; replay without duplicates | Failure and recovery · runs/20261015T033503Z-f6539b3bc938 |
| 8 | 3:33 | Human correction and policy revision | Human review, correction and policy revision |
| 9 | 4:17 | Architectural tradeoff; published series | Tradeoff · published series |

## Narration

**1. Topic and audience** (0:00)

This is a technical demonstration of Before the Merge, a pipeline that collects recent sources, uses an AI model for editorial decisions, and produces a three part series for technical leads of small software teams deciding how much work to delegate to coding agents.

**2. Configuration (topic, sources, policy, prompts)** (0:18)

The topic, the sources, the editorial policy and the four model prompts live in their prescribed configuration files. The sources cover RSS feeds, YouTube videos and podcasts, from independent publishers, and every run takes a snapshot of this configuration so later edits never rewrite an earlier run.

**3. Architecture and entry point** (0:40)

The entry point is run_local.sh, which sets up the local Ollama model and calls run.sh. Run dot S H only coordinates. It calls the collection workflow, which runs the three collectors, extraction, the evidence store and the thirty day filter, and then the series workflow, which runs selection, briefs, articles, video scripts and the content check. Each of the sixteen required scripts owns one job, reads and writes JSON Lines, and writes a receipt to the run's log folder. Only store.sh opens the SQLite evidence index. The pipeline stops at awaiting review, and packaging happens only after a human approval that matches the current review_id.

**4. Run 1 results and human approval** (1:27)

The first live run, on the fifteenth of October, found twenty eight eligible items, eighteen written, five podcast and five YouTube, from ten publisher groups. The model accepted twenty five, rejected two and deferred one, then wrote three briefs, three articles and three scripts. The content check passed, I reviewed the drafts, wrote the approval, and the package was produced.

**5. Trace one source → decision → published claim** (1:51)

Here is one published claim traced back to its evidence. Article one quotes Jake Cukjati saying the agents test everything and implement it. The brief records that as claim 01-c1, a source claim, pointing to the YouTube item, an exact version hash and segment s-000096. The decisions file shows the item was accepted for pieces one and two. The stored version shows the original publication date, the ninth of October, separately from the retrieval date. And the retained transcript gives the exact words at six minutes and ten seconds.

**6. Second run: new / unchanged / duplicates / 30-day window** (2:30)

The second live run used the next UTC date and the same evidence store. Twenty items were recognised as unchanged and were not processed again, and there were no duplicate records. Three items published on the fifteenth were detected as new: two GitHub changelog posts, which the model accepted, and a Cloudflare post, which it deferred. The thirty day window moved by one day, but the oldest item is from the nineteenth of September, so nothing was excluded.

**7. Failure reporting and recovery; replay without duplicates** (3:00)

The system also reports failures instead of hiding them. In an earlier collection attempt, the GitHub feed contained XML the parser rejected. The feed collector exited with an error, the run was marked incomplete, and the other collectors still completed. After the parser was fixed, the retry was recorded separately and the original failure receipt was kept. A labelled replay of the saved inputs produced no new and no changed items, which shows the store handles repeated input without duplicates.

**8. Human correction and policy revision** (3:33)

I reviewed three accepted and three rejected or deferred decisions against the source passages, and disagreed with four. One correction mattered most: a brief presented a sponsor advertisement for Blitzy, claiming 80% of software epics are delivered autonomously, as a podcast finding. I relabelled it as an advertisement. I then revised the policy and reran selection on the same items. The policy changed the counts, but it did not reliably fix the reviewed cases, and run two even repeated a vendor claim I had removed. So run two was not published. The real bottleneck is excerpt retrieval, and human review remains a required step.

**9. Architectural tradeoff; published series** (4:17)

The main architectural tradeoff is immutable, content addressed evidence behind a single store interface. It costs extra storage and validation, and conservative identity matching leaves some copies for human review. In return, every published claim can be traced to the exact passage that supported it, and running the pipeline again does not duplicate anything. The three articles and their videos are published and linked to each other. Thank you for watching.

