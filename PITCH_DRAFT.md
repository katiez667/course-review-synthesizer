# Course Review Synthesizer — Pathfinders Challenge Draft

*Category 01: Degree Planning & Discovery. This is a DRAFT — every number here is
pulled live from the repo as of 2026-08-18, but the framing/voice is mine, not yours.
Edit freely, cut what doesn't sound like you, and check every claim against the demo
before you submit it.*

---

## The one-liner

**The answer you wish Google gave you when you search "is 15-150 hard."**

Stellic tells you what you still need. RateMyProfessors and FCE give you the basic
stats. Then you're on your own — hunting the real, qualitative truth across Reddit,
RateMyProfessors, and course-review blogs, and reconciling it yourself. This tool
does step three: it fuses what those scattered sources say, synthesizes it into one
grounded answer, and cites every claim back to where it came from.

## 1. Real student problem

Every CMU student has done this: open five Reddit threads and an RMP tab, skim for
twenty minutes, and still not be sure if the "workload is brutal" comment is from
2019 or last semester, or which professor it's even about. The information exists.
Nobody has reconciled it.

## 2. Originality — synthesis, not aggregation

Every existing tool — RateMyProfessors, Coursicle, FindMyProfessors, the Chrome
extensions that inject RMP scores into registration — hands you reviews to *read*.
None of them fuse RMP's structured signal with Reddit's candid, course-specific
texture into one answer. None of them cite their sources. None of them refuse to
average away a real disagreement.

That last point is the wedge, and it's not a slogan — it's an enforced invariant.
For 15-150, the corpus has two professors with genuinely opposite profiles:

| | Quality | Would take again | Difficulty |
|---|---|---|---|
| **Erdmann** | 4.1/5 | 77% | 3.5/5 |
| **Brookes** | 2.1/5 | 0% | 4.6/5 |

Averaged, that's a forgettable 3.1/5. Reported separately — which is what the demo
actually does, unconditionally — it's the single most decision-relevant fact a
student could get before registering. The product is built so this *can't* regress:
professor panels are rendered independently, never blended, with their own citations.

**Citations are a hard gate, not a suggestion.** Every synthesized answer is checked
against the retrieved evidence before it's shown — an answer that cites a passage
never actually retrieved gets caught, the model is told exactly which ids were
invented, and it's given up to two more attempts. If it still can't ground itself,
the system raises rather than displays an unverifiable answer. Base rate before the
gate: roughly 1 in 16 runs invented a citation — always a real-*looking* id from a
real naming pattern, not gibberish, which is exactly the failure mode a demo could
otherwise miss.

## 3. Scale potential — school-agnostic, and provably so

The corpus isn't limited to a hand-picked showcase set. As of today it holds
**264 chunks across 109 CMU courses**, pulled from Reddit, RateMyProfessors, and
course-review blogs — not just the 7 courses frozen into the polished demo.

To prove the pipeline generalizes rather than just asserting it, there's a second,
live mode: pick literally any of those 109 courses, and the same retrieve →
synthesize → citation-gate pipeline runs in real time and produces a cited card on
the spot, built from evidence the retriever finds itself. Nothing about the
pipeline — the retrieval, the professor-split logic, the citation gate — is CMU-
specific; it's the corpus that's CMU because that's what's checkable in a demo.
Point it at another school's Reddit/RMP data and the architecture doesn't change.

## 4. Design / experience

The whole pitch fits in one contrast: ten tabs vs. one card. The demo makes that
concrete —

- **Search, not a form.** Type a course code or a title fragment ("func" finds
  Principles of Functional Programming); nothing dead-ends — a query that matches
  nothing falls back to the full course list instead of a blank screen.
- **The card itself.** One headline answer, tabbed facets (workload, difficulty
  type, structure, worth-it, comparisons, co-scheduling), a source-mix bar showing
  the reddit/RMP/blog split, and an expandable receipts drawer where every citation
  is clickable and jumps to its source passage.
- **Verified vs. pending is visible, not hidden.** A citation with no fetchable URL
  renders "link pending" rather than a fabricated link — 19/30 of 15-150's receipts
  are verified with real URLs; the other 11 are honestly marked, not silently upgraded.

## 5. Build quality

- **RAG over a real corpus**, not a mock: sentence-level chunking, semantic
  embedding retrieval, optional recency weighting, and per-facet retrieval (each
  card facet is its own retrieval query against the same corpus, not one
  answer sliced up after the fact).
- **The citation gate fails closed.** It's not a linter running after the fact —
  `synthesize()` cannot return an ungrounded answer to the UI at all; it raises.
- **Provenance is real, not decorative.** Numeric stats (quality, difficulty,
  would-take-again %) are parsed out of RMP text and injected structurally, never
  embedded as strings, because "4.1/5" doesn't retrieve usefully as a sentence.
- **The frozen demo makes zero API calls.** Seven cards, each already synthesized
  and already past the citation gate, served as static JSON — so the polished demo
  can't fail, drift, or cost anything mid-pitch. The live mode is a separate,
  explicit surface precisely so the guaranteed-to-work demo and the
  prove-it-generalizes demo never depend on each other.

---

## What's demonstrably true right now (for the write-up's claims section)

- 264 evidence chunks, 109 CMU courses, 3 sources (Reddit/RMP/blog)
- 7 frozen, fully-cited course cards + 1 four-way comparison card
- All three core query types work: single-course difficulty, X-vs-Y comparison
  (10-301/315/601/701), and co-scheduling ("can I take 150 and 213 together")
- Professor-split enforced for 15-150 (Erdmann vs. Brookes, never averaged)
- Citation audit gate: catches invented citations pre-display, ~1/16 base rate
  without it, 0 shown to a user with it
- Live compile mode: any of the 109 corpus courses, not just the curated 7

## Known, honest limitations (say these before a judge finds them)

- Professor-split panels currently only render for 15-150 — the structured
  instructor-stats lookup is pinned to that course's two professors as a demo
  seam, not generalized to all 109 yet. The retrieval and synthesis logic
  underneath is already school/course-agnostic; this one lookup table isn't.
- Professor names aren't normalized across sources yet (e.g. "Pat" vs. "Pat
  Virtue"), which is what the above limitation is downstream of.
- The corpus is deliberately curated/cached for the demo window, not a live
  ingestion pipeline — matches the "honest demo strategy" every judged RAG
  project should follow, and is explicitly the MVP scope, not a shortcut.

