# Pathfinders Project Knowledge — Course Review Synthesizer

*Reference doc for the Stellic Pathfinders Challenge. Category 01: Degree Planning & Discovery. Window: July 20 – Aug 21, 2026. Built new, solo, with Claude API credits.*

---

## 1. Product thesis (refined)

Course planning is really three steps:

1. **Stellic** tells you *what requirements you still need.*
2. **ScottyLabs / FCE** tells you *the basic stats* — workload hours, aggregate ratings.
3. **Then you're on your own** — hunting the qualitative, experience-based truth across RateMyProfessors, Reddit, Discord, and group chats.

Steps 1 and 2 are solved. **Step 3 is not.** The information is scattered, unstructured, and self-selected, and you have to read dozens of comments across multiple sites and reconcile them yourself.

**Target: collapse step 3.** A tool that gathers scattered course/professor reviews from public sources and synthesizes them into a grounded, cited, personalized answer to the student's actual question. **School-agnostic by design.**

The one-line framing: *the answer you wish Google gave you when you search "is [course] hard."*

---

## 2. Why school-agnostic is the right call

- RMP covers ~2M+ professors across essentially every US/Canada school; most campuses have a per-school subreddit. Both sources generalize, so nothing is hardcoded to CMU.
- "Scale potential" is one of five equally weighted judging criteria. A tool that works anywhere has a real scale story; a CMU-only aggregator does not.
- You can still *demo* on CMU (you can verify the output because you know the courses), while the architecture stays general.

---

## 3. Competitive landscape and the wedge

**Existing tools and their shared blind spot:**

- **RateMyProfessors** — incumbent. Structured signal (quality, difficulty, would-take-again %, tags) + free-text reviews. Professor-centric, read-it-yourself, no synthesis, no Reddit.
- **Coursicle** — largest RMP alternative (~12M reviews / 2M professors), plus scheduling. Still read-it-yourself, professor-centric, no cross-source synthesis, no Reddit.
- **School-specific sites** — PolyRatings (Cal Poly), Bruinwalk (UCLA), CourseTable (Yale), Berkeleytime (Berkeley), Atlas (Michigan). Deep but single-school.
- **FindMyProfessors** — search by *course* instead of professor; still just surfaces RMP data.
- **Chrome extensions** — inject RMP scores into a school's registration page.
- **Study tools** (NotebookLM, Studocu) — adjacent; they summarize *your own* materials, not *others'* reviews.

**The gap nobody fills:** every tool above hands you reviews to *read*. None *synthesize across sources*, and none touch Reddit, where the most tactical, course-specific lore lives ("don't take X with Y," the real curve, hidden prereqs). RMP is professor-centric and sanitized; Reddit is course-centric and candid.

**The wedge = fuse the sources → synthesize → cite → personalize.** Answer the student's actual question by drawing on structured signal *and* qualitative texture, grounded in citations, shaped by the student's context.

---

## 4. Where students actually look — the source map

The real behavior: a student types "is [course] hard" into a browser and gets a scattered pile — a Reddit thread, an RMP page, a Quora answer, a YouTube video — none talking to each other. Your product is the thing that *should* come up. This also implies an ingestion model: a **search → fetch → synthesize** pipeline that pulls whatever the web surfaces per course, rather than only fixed API integrations.

**Objective / structured signal**
- **Grade distribution platforms** — the most underused high-signal source; students want the *objective* difficulty number. Berkeleytime and Michigan's Atlas are the models. Atlas shows grade distributions, evaluations, workload ratings, requirement-vs-elective split, and *courses commonly taken in the same semester* (a primitive version of the co-scheduling answer). These are school-internal — most schools lack one, which is the opening.
- **Public syllabi** — reveal real assessment structure and workload; often googlable; underrated corpus.
- **RateMyProfessors** — structured tags + free text.

**Candid free-text**
- **Reddit** — per-school subs plus major/topic subs.
- **Discord servers** — most current and candid, but near-impossible to scrape and privacy-fraught. Use as inspiration for *what to answer*, not a data source.
- **Quora & College Confidential** — "is X hard at Y" Q&A, often detailed.

**Social / video**
- **YouTube** — "classes to avoid," "day in the life of an X major," lecture-style clips; transcripts are fetchable and rich.
- **TikTok / Instagram** — first stop for many younger students; a whole professor-research genre.

**School-internal tools**
- **FCE / ScottyLabs, Atlas, Berkeleytime, Coursicle** — deep but siloed. Strategic point: build the *Atlas experience* for the ~95% of schools that lack one, assembled from public sources.

---

## 5. Data access reality — build honestly around this

### RateMyProfessors
- No official API, but a stable **unofficial GraphQL endpoint** with maintained open-source wrappers: Python (`RateMyProfessorAPI`, `rmp_client`), TypeScript (`Michigan-Tech-Courses/rate-my-professors`).
- Data: avg quality, difficulty, would-take-again %, department, tags, and dated free-text reviews.
- **ToS:** gray area. Public data; personal/research use tolerated; scraping at scale / redistribution / commercial use is against ToS and risky. For the demo → bounded pull via a wrapper, cached, disclosed.

### Reddit
- **$0.24 / 1,000 calls** commercial; **free tier = 100 queries/min** (OAuth).
- **Nov 2025 "Responsible Builder Policy":** pre-approval now required even for personal projects; ML use explicitly restricted.
- Historical data: Pushshift dead for general devs; successors are **Project Arctic Shift** (dumps + limited API) and **Academic Torrents** dumps.

### Honest demo strategy (scores well on "how well it's built")
Demo on a **cached, curated corpus** for ~15–30 courses at one school. In the write-up, describe the at-scale ingestion pipeline and its legal constraints explicitly.

---

## 6. Core query types — the product spine

These three questions are what *no existing tool answers in one shot*. They should drive the corpus schema and the demo script:

1. **"Is [course] difficulty?"** — the *synthesis* case. Value = collapsing ten tabs into one grounded, cited answer.
2. **"[Course X] vs [Course Y]?"** — the *comparison* case. RMP/Coursicle are single-professor pages and structurally can't do this. Great demo moment.
3. **"Can I take [X] and [Y] together?"** — the *workload-compatibility* case; hardest and most valuable. Atlas only shows what people *happen* to co-take; nobody answers whether the combined load is survivable given the student's context. Reasoning over both courses' workload signals + student profile ("both peak mid-semester, both project-heavy — doable but brutal") is something no platform does.

**Trust feature:** students' top complaint about existing reviews is that they're extreme, self-selected, and often years old (or for a different section). Weighting recent reviews higher and flagging self-selection bias directly answers that objection — and plays to the cog-sci angle on how self-selected samples distort judgment.

---

## 7. Mapping to the five judging criteria (equal weight)

- **Real student problem** — step 3 is universally felt; you live it.
- **Originality** — synthesis + multi-source fusion + citations + personalization; nobody does this — *if you lead with synthesis, not aggregation.*
- **Scale potential** — school-agnostic; works anywhere the sources exist.
- **Design / experience** — one clean sourced answer beats ten tabs; that contrast *is* the demo.
- **Build quality** — RAG over a real corpus with grounded citations.

---

## 8. Suggested MVP scope (3-week window)

**In:** curated corpus (~15–30 courses at one school: RMP + a few Reddit threads + grade data where available); RAG pipeline (embed → retrieve → Claude synthesizes with citations); lightweight personalization (major, year, workload tolerance, current courses); clean frontend (query box + synthesized answer + expandable "what students said" + course card). Serve the three core query types.

**Out (v2):** live ingestion at scale, multi-school switching UI, full semester-load simulator, historical trends.

**Architecture note:** at this scale, embeddings + SQLite or in-memory is plenty; Claude does synthesis + citation. Wire Claude API credits in via Claude Code.

---

## 9. Open design decisions

- Interaction model: query-first (chat) vs. course-first (card) — or both?
- Demo school: CMU (easiest to verify).
- Attribution/privacy: paraphrase + link Reddit content; don't republish usernames prominently.
- Opinionation: neutral synthesis vs. explicit "recommend / avoid."
- Bias surfacing: flag self-selection and recency caveats in the answer.

---

## 10. Course card — facet schema

The course card is the **cache unit**, and each facet is a **separate retrieval target** with its own evidence. Retrieval isn't one job; it's one job per facet. Facets (derived from the 15-150 test batch):

1. **Workload & time** — hours/week and ramp-up spikes. *(150: assignments short but time-consuming; ramps at staging / continuations / two-player games.)*
2. **Difficulty type** — conceptual vs. grindy. *(150 "hard on the brain," few lines of code; 122 more typing and debugging.)*
3. **Professor quality (per-instructor)** — attribution is mandatory. *(Erdmann 4.1 / 77% would-take-again vs. Brookes 2.1 / 0%.)*
4. **Course structure** — lectures, TA/OH quality, assignments, exams. *(150 heavily TA/OH-driven; exam complaints tied to Brookes.)*
5. **Enjoyableness / experience** — subjective texture. *("fun class though"; "favorite CS class I've taken.")*
6. **Key takeaways / what you learn** — durable skills. *(recursion ≡ induction; FP mindset; map/reduce.)*
7. **Worth / value** — career relevance, opportunity cost, what it unlocks. *("useless unless Jane Street" vs. "least fun but most important.")*
8. **Best-fit / who should take it** — prerequisite mindset. *("if inductive proofs come naturally, do 150.")*
9. **Comparisons** — vs. sibling courses. *(150 vs. 122; 150 vs. 112.)*
10. **Co-scheduling / pairing** — take-with / avoid-with. *(150+213 vs. 150+251; "both cooked combos.")*
11. **Recency / drift flag** — course changed over time. *(150 ≈ the old 15-212; fall vs. spring instructor differences.)*

The card = these facets, each backed by cited evidence. "Worth" (facet 7) was the missing piece — it's what students actually chase and what pure aggregators never surface.

---

## 11. Retrieval test protocol

**Principle: a retrieval test judges the *evidence fetched*, not the final answer.** Inspect the retrieved chunks *before* synthesis. Separate the two failure modes: evidence-not-fetched (retrieval problem) vs. evidence-fetched-but-answer-weak (synthesis problem). Debugging the wrong layer wastes days.

The six tests (run against the 15-150 batch):

1. **Facet coverage** — per facet, does retrieval surface the decisive evidence?
2. **Professor split** *(the critical one)* — "is 150 hard / who to take it with" must surface **both** Erdmann and Brookes **with attribution intact.** Flattening them into one average is the exact failure that kills the wedge.
3. **Comparison** — "150 vs. 122" must pull the *direct-comparison* threads, not 150-only chunks.
4. **Co-scheduling** — "150 + 213 together?" must pull the *pairing-specific* threads.
5. **Signal vs. noise** — "takeaways from 150" must surface the genuine takeaways and ignore the lambda-performance flame war.
6. **Staleness** — dates survive retrieval; drifted/old content is down-weighted or flagged.

**Scoring:** per query, list the 3–5 must-surface facts, run retrieval, count hits / misses / junk. Two numbers matter at this scale — recall of must-have facts, and professor-attribution pass/fail. Skip fancy IR metrics.

**The decisive A/B:** run every query two ways — (a) live search + fetch, (b) embed-and-retrieve over the cached batch — and compare. This settles the architecture question: reliable live retrieval → lean live-agent; noisy or missing pairing threads → lean cached corpus with live as fallback.

---

## 12. Sources

- RMP GraphQL Python client — https://amaanjaved1.github.io/Rate-My-Professors-API-Client-Python/
- RMP GraphQL TS wrapper — https://github.com/Michigan-Tech-Courses/rate-my-professors
- RateMyProfessorAPI (PyPI) — https://pypi.org/project/RateMyProfessorAPI/
- FindMyProfessors — https://devpost.com/software/find-my-professors
- Reddit API pricing & rate limits (2026) — https://www.socialcrawl.dev/blog/reddit-data-api-2026
- Reddit Responsible Builder Policy — https://redreplier.com/en/blog/reddit-api-pricing
- Coursicle — https://www.coursicle.com/professors/
- Michigan Atlas (about) — https://atlas.ai.umich.edu/about/
- Berkeleytime — https://berkeleytime.com/grades
