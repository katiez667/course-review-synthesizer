# CLAUDE.md

RAG pipeline that answers CMU course-selection questions from scattered public reviews
(Reddit, RateMyProfessors, student course-review blogs) with grounded, cited synthesis.
Built for the Stellic Pathfinders Challenge — see `pathfinders_project_knowledge.md` for
product thesis, the 11-facet course-card schema, and the retrieval test protocol.

The wedge is **synthesis, not aggregation**: every other tool hands you reviews to read.

## Data flow

```
corpus_15150.py      blog_corpus.json   rmp_corpus.json   reddit_corpus.json
(58 hand-pasted)     (150)              (20)              (29)
        └────────────────┴──────────────────┴──────────────────┘
                              │
                    corpus_all.py  _norm() -> CORPUS (257 chunks, 109 courses)
                                   provenance() / cite()   <- citation layer
                              │
                    retrieval_spike.py
                      split on id.endswith("-summary"):
                        -> PROFESSOR_STATS  (parsed, held OUT of embeddings)
                        -> RAW (255) -> sentence_chunk(240) -> PASSAGES (414)
                      retrieve(): filter pool -> score -> optional recency -> top-k
                              │
                    synthesize.py
                      get_bundle / get_multi_bundle -> _pack (attaches provenance)
                      -> SYSTEM prompt -> claude() -> audit_citations gate
                              │
                    freeze_cards.py   37 gated calls, ONE TIME
                              │
                    demo_data/*.json  (7 frozen cards — the demo reads only this)
                              │
                    CourseCard.jsx    display only, no API, no re-derivation
```

Layer boundaries matter: `corpus_all` normalizes, `retrieval_spike` retrieves,
`synthesize` grounds. The split exists so you can debug the right layer —
evidence-not-fetched (retrieval) vs evidence-fetched-but-answer-weak (synthesis).
Judge retrieval by inspecting retrieved chunks *before* synthesis.

## Chunk schema

`corpus_all._norm()` is the contract. Ten keys on every chunk, regardless of source:

| key | notes |
|---|---|
| `id` | **`-summary` suffix is load-bearing** — routes to `PROFESSOR_STATS` instead of the embedding pool |
| `source` | `reddit` \| `rmp` \| `blog` — drives the `provenance()` label |
| `course` | defaults `"15-150"` (the 15-150 batch has no course field) |
| `thread` | falls back to `blog · {author}` so `thread_filter` never hits `None` |
| `professor` | genuinely `None` (JSON null) on 134/257 |
| `date` | **heterogeneous on purpose**: `"6y"`, `"2026-03"`, `"Fall 2023"` — normalized late by `parse_year()`, which covers all three forms; **0/257 chunks fail to parse**, so nothing silently takes the `0.85` fallback weight |
| `role` | flair, e.g. `"Junior (CS)"` |
| `author` | blogs/reddit only |
| `url` | `None` for hand-pasted Reddit **by design** |
| `text` | verbatim |

`retrieval_spike` derives a wider shape: `{**chunk, pid: "id#i", year, passage}`.
**`pid` is the citation unit** — `_pack` emits it as `id`, and the audit gate keys on it.

## Two invariants — do not regress these

1. **Never invent a URL.** Hand-pasted Reddit chunks have no verified link and must render
   `link pending`. `provenance()` sets `verified: bool(url)`; `_backfill_url` fills RMP
   profile links from `RMP_PROFILE` and otherwise returns `None` on purpose.
2. **Never average professors into one verdict.** Erdmann (4.1/5, 77% would-take-again) and
   Brookes (2.1/5, 0%) must be reported separately with their own stats and reviews.
   Flattening them is the exact failure that kills the product wedge.

Numeric stats are **parsed out of the text and injected**, never embedded — a "4.1/5" string
doesn't embed usefully.

## Citation gate (fail closed)

`synthesize()` is gated: call -> `audit_citations` -> retry with a correction naming the
invented ids and re-listing valid ids -> cap 3 attempts -> raise `CitationAuditError`.
It raises rather than returning text so a bad answer can't be displayed.
`synthesize_once()` is the ungated version, for debugging only.

**The only check is id-in-bundle.** Do not add a course-match or professor-match constraint.
Comparison and co-scheduling chunks legitimately discuss courses other than their own
`course` field (e.g. a 10-315 comment that compares against 10-701), and a stricter gate
would break exactly the disambiguation queries the product exists to answer.

Base rate before the gate: ~1 in 16 runs invented citations — always *real corpus ids that
were not retrieved*, inferred from the `rmp-{prof}-{NN}#0` naming pattern. That is the
dangerous shape: the citation looks legitimate and points at a real review.

## Retrieval: two different course filters

```python
retrieve(query, course="10-301")        # exact match on the `course` METADATA field
retrieve(query, course_filter=["213"])  # token match on passage/thread TEXT
```

Both exist deliberately. `course=` scopes to chunks *about* a course — note the Reddit text
often writes `10301` without a hyphen, so token matching fails there. `course_filter=` finds
chunks that *mention* a course, which is what the T4 co-scheduling test needs
("can I take 150 and 213 together" wants pairing chunks whose `course` is 15-150).

## Running

```bash
python corpus_all.py                 # corpus stats by source/course
python retrieval_spike.py            # NOTE: __main__ runs synthesis, not main()
python -c "import retrieval_spike as r; r.main()"   # the 6-test retrieval harness
python synthesize.py                 # bundle + provenance, no model call
```

`embed_texts` memoizes the `SentenceTransformer` in `_ST_MODEL`, so the model loads once
per process instead of once per `retrieve()` call. Pure cache — ranking is unaffected.

Model seam: `synthesize.claude()` — `claude-sonnet-4-6`, `max_tokens=16000`,
`thinking={"type":"adaptive"}`, `output_config={"effort":"medium"}`.
On Sonnet 4.6: `budget_tokens` is deprecated (use adaptive) and assistant-turn prefills
return a 400. Never hardcode a key — `anthropic.Anthropic()` resolves `ANTHROPIC_API_KEY`
from the environment.

**Gotcha:** if `ANTHROPIC_BASE_URL` is set in the shell it points at a proxy that will
reject a normal API key. Unset it for direct calls: `env -u ANTHROPIC_BASE_URL python ...`

## Card library layer (was: "frozen demo")

**One surface, two card sources.** There is no longer a separate frozen demo and live
demo — `preview.html` is the only page, and it shows a *library* of cards that grows as
courses are searched:

| dir | role | written by |
|---|---|---|
| `demo_data/` | curated seed, 7 cards | `freeze_cards.py` only — **never** at runtime |
| `card_cache/` | compiled on demand + `_meta.json` (hits, timestamps) | `live_server.py` |

Presented as one list; split on disk so a runtime bug can't corrupt the curated set.
`live_server.py` refuses (409) any attempt to overwrite a `demo_data/` card.

**A card is compiled at most once, ever.** First search for a course = one gated call;
every later open is a cache hit at zero cost, counted in `_meta.json` and surfaced in the
UI ("N opened from cache, N API calls avoided"). That caching model *is* the scale story.

`preview.html` picks its mode automatically: with `live_server.py` running it can compile
new courses; against a plain `python3 -m http.server` it degrades to browse-only over the
two card dirs, so the demo still opens if the API is down.
Re-freezing is a deliberate, billable act — **don't run `freeze_cards.py` casually**:

```bash
env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='...' python3 freeze_cards.py
```

37 gated calls, ~12 min, and it overwrites every card. Cards:

| file | shape | notes |
|---|---|---|
| `15-150.json` | single, 6 facets | **the only card with a professor split** (Erdmann `seek_out` / Brookes `avoid`), and the only one with unverified receipts (11/30) |
| `15-213`, `15-251`, `15-410`, `15-451`, `85-102` | single, 4 facets | `professor_split.available: false` — see the pinned-`PROFESSOR_STATS` gap below |
| `ml-4way.json` | multi, 4 facets | `get_multi_bundle` over 10-301/315/601/701, plus a `per_course` map |

Each card carries one gated answer per tab (`headline` + `facets[]`), a `receipts` map keyed
by **pid**, a per-card `source_mix`, and `professor_split`. Two things are computed **once at
freeze time and stored** so the UI never re-derives them: the `seek_out`/`avoid` verdict
(`quality >= 3.5 && would_take_again_pct >= 50`) and `source_mix`. Facet keys/labels come
from the 11-facet schema in `pathfinders_project_knowledge.md` §10, trimmed to what the
evidence supports.

`get_bundle` / `get_multi_bundle` take a `recency=` passthrough (default `False`) that
forwards to `retrieve()`. The frozen cards were built with `recency=True` — a soft age-decay
prior on the similarity score, never a filter.

**Gotcha:** `cross_course_citations` is **always empty and cannot fire**. `get_bundle` filters
with `p["course"] == course`, so every chunk in a bundle carries that course by construction.
It is not a safety check — treat it as dead weight unless a bundle is ever built with
`course_filter=` instead. To actually find comparison/co-scheduling evidence, key on course
numbers **named in the chunk text** (a chunk comparing 150 to 213 is still `course: 15-150`);
`PHASE_D_cross_course.md` has that table and the regex caveats — bare `100` is a lab score,
not a course.

Viewing: the repo has no bundler. `preview.html` loads React from a CDN, strips the two
module imports out of `CourseCard.jsx`, and compiles it together with its own inline app
(`#app-src`) in one Babel pass — so the component itself
stays a normal ES module you can drop into Vite/Next unchanged. Needs http, not `file://`:

```bash
# full mode (search any course, compile on demand — needs a key):
env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='sk-...' python3 live_server.py
# browse-only mode (existing cards, no compiling, no key):
python3 -m http.server 8000
# either way: http://localhost:8000/preview.html
```

`live_server.py` binds 127.0.0.1 only and resolves the key from its own environment —
the browser never sends or sees it. `/api/compile` is the sole billable endpoint;
`/api/card` and `/api/preview` never spend.

## Free-text questions (`answer_index.py`)

`preview.html`'s box takes a question, not just a course code. `GET /api/ask?q=...`
embeds the query and matches it against the **stored `question` string of every tab of
every existing card** (~37 across the seed set) — so an answer comes back instantly with
its citations and **no model call ever**. This is retrieval over cached *answers*, not
new synthesis.

Two things it must keep doing:
- **Embed question + course codes + title.** The facet questions are formulaic
  (`how many hours a week does {course} take`), so without the title
  "how long does functional programming take" matches whichever course phrases its
  workload question closest instead of 15-150.
- **Refuse when a named course has no card.** If the query names a course code and no
  card covers it, `good_match` is forced `False` and a `compile_hint` is returned —
  otherwise "is 15-712 hard" confidently answers out of the 15-150 card. Same
  fail-closed instinct as the citation gate.

`MATCH_THRESHOLD = 0.45` was tuned against a 9-query set (6 should-match, 3 should-not).
The index rebuilds only when card files/mtimes change, and `/api/compile` forces a
rebuild so a new card is askable immediately.

## Known gaps (unfixed, by choice)

- **Professor names aren't normalized across sources.** 10-315 has both `"Pat"` (blog) and
  `"Pat Virtue"` (Reddit); 15-150 has `"Erdmann"` vs `"Michael Erdmann"`. An exact-match
  `professor=` filter treats them as different people. This is what will bite when
  `PROFESSOR_STATS` gets unpinned.
- **`PROFESSOR_STATS` is pinned to Erdmann/Brookes.** `get_bundle` iterates it to decide
  which professors exist, so the professor-split path only works for 15-150 regardless of
  the `course` argument. Main thing standing between this and the school-agnostic claim.
- **Some Reddit URLs are thread permalinks, not per-comment deep links**
  (e.g. `reddit-15213-v16yce-op`). Verified, but coarser than its siblings.

## Editing notes

- `synthesize.py` (15x) and `corpus_all.py` (6x) contain **literal `\uXXXX` escape
  sequences** in source — the six characters `\u00b7`, not the `·` character itself.
  String-replace edits must match the literal backslash form or they silently fail to match;
  patch via a Python script if the edit tool keeps normalizing them.
- `retrieval_spike.py` has its own legacy `get_chunks_for_synthesis` + `synthesize` with a
  hardcoded Anthropic call. The live path is `synthesize.py`; don't confuse the two.
- Reddit content: paraphrase and link, don't republish usernames prominently.
- Never commit `.env` (already gitignored). Never write an API key into a repo file.
