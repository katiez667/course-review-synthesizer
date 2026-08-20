# Course Review Synthesizer

**The answer you wish Google gave you when you search "is 15-150 hard."**

Built for the Stellic Pathfinders Challenge — Category 01: Degree Planning & Discovery.

Course planning has three steps. Stellic tells you which requirements you still need.
FCE and RateMyProfessors give you the averages. Then you're on your own, reconciling
scattered opinions across Reddit, RMP, and student blogs that don't agree with each
other. This closes step three: it fuses those sources into one grounded, cited answer.

The wedge is **synthesis, not aggregation** — every other tool hands you reviews to read.

---

## Quickstart

No build step, no bundler. Python 3.9+ and a browser.

```bash
pip install sentence-transformers anthropic requests scikit-learn
```

**Browse the card library** (no API key, nothing billable):

```bash
python3 -m http.server 8000
```

**Full mode** — search any course, compile new ones on demand:

```bash
env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='sk-...' python3 live_server.py
```

Either way open <http://localhost:8000/preview.html>.

> `live_server.py` binds to 127.0.0.1 only and reads the key from its own environment —
> the browser never sees or sends it. `/api/compile` is the only endpoint that spends.

---

## What it does

**Never averages professors.** 15-150 has two instructors with opposite profiles.
Reported separately, always — flattening them into one number is the exact failure that
destroys the product's value:

| | Quality | Would take again | Difficulty |
|---|---|---|---|
| **Erdmann** — seek out | 4.1/5 | 77% | 3.5/5 |
| **Brookes** — avoid | 2.1/5 | 0% | 4.6/5 |

**Citations are a gate, not decoration.** Every synthesized answer is audited against the
evidence it was given. An answer citing a passage that was never retrieved is rejected,
the model is told which ids it invented, and it retries — capped at three attempts, then
it raises rather than displaying an unverifiable answer. Base rate before the gate was
roughly 1 in 16 runs, always *real-looking* ids inferred from the naming pattern.

**Never invents a link.** Hand-pasted Reddit chunks have no verified URL and render
`link pending` rather than a fabricated one. 19 of 15-150's 30 receipts are linked; the
other 11 say so.

**Compiled at most once, ever.** The first search for a course pays one gated API call.
Every later open is a cache hit at zero cost, counted and surfaced in the UI. Free-text
questions are matched against the questions existing cards already answer, so a question
like *"can I take 150 and 213 together?"* returns instantly with citations and **no model
call at all**.

---

## How it fits together

```
corpus_15150.py  blog_corpus.json  rmp_corpus.json  reddit_corpus.json
        └──────────────┴────────────────┴────────────────┘
                            │
                     corpus_all.py        normalize + provenance/citation layer
                            │
                   retrieval_spike.py     sentence chunking, embedding retrieval,
                            │             optional recency weighting
                      synthesize.py       evidence bundle -> Claude -> citation audit
                            │
              freeze_cards.py  /  live_compile_demo.py
                            │
              demo_data/ (seed)  +  card_cache/ (on demand)
                            │
             preview.html + CourseCard.jsx   display only, no re-derivation
                            │
                     answer_index.py        free-text Q -> cached answer, no model call
```

`CLAUDE.md` documents the layer boundaries, the two invariants, and the known gaps.

---

## Honest limitations

- **The professor split only renders for 15-150.** The structured instructor-stats lookup
  is pinned to that course's two professors. The retrieval and synthesis beneath it are
  course-agnostic; this one lookup table isn't.
- **Professor names aren't normalized across sources** ("Pat" vs "Pat Virtue"), which is
  what the above is downstream of.
- **The corpus is curated and cached**, not live ingestion — 264 chunks across 109 CMU
  courses. Most courses have thin coverage; the UI warns before compiling a card whose
  evidence all comes from a single source.
- **Free-text answering is retrieval over cached answers**, not open-ended QA. When a
  question names a course with no card, it refuses and offers to build one rather than
  answering from a different course.

## A note on the data

The corpus contains excerpts of publicly posted student reviews from Reddit,
RateMyProfessors, and personal course-review blogs, collected in a bounded, cached pull
for a student project and retained with attribution and source links. Reddit content is
paraphrased and linked rather than republished with usernames. RateMyProfessors has no
official API; this uses the same public GraphQL endpoint the open-source wrappers use.
Redistribution at scale or commercial use would need a different arrangement with those
platforms.

