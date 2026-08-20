# Phase D — cross-course review aid

Two checks. The first is the one that was asked for; the second is the one that
actually carries signal, because the first turns out to be vacuous by construction.

## 1. Cited chunk whose `course` METADATA FIELD differs from the card

| card | tab | cited chunk | chunk course |
|---|---|---|---|
| _(none — on any card, including ml-4way)_ | | | |

**0 rows.**

This is empty *by construction*, not by luck. `get_bundle` filters the pool with
`p['course'] == course`, so every chunk in a single-course bundle carries that
course by definition; `get_multi_bundle` scopes each sub-bundle the same way, so
every ml-4way chunk carries one of the four. **A course-field mismatch cannot occur
under the current retrieval path**, which is why nothing showed up on the ML card.
The check only becomes live if a bundle is ever built with `course_filter=` (token
match on text) instead of `course=` (metadata) — the T4 co-scheduling path.

## 2. Cited chunk that NAMES another course in its text

Same intent, but keyed on chunk *content* rather than the metadata field. This is
where the comparison and co-scheduling evidence actually lives — and it is invisible
to check 1, because a chunk that compares 15-150 to 15-213 is still `course: 15-150`.

| card | cited chunk | chunk course | other courses named | tabs it appears on |
|---|---|---|---|---|
| 15-150 | `pair-03#0` | 15-150 | 15-210, 15-213, 15-251 | overview, worth, co_scheduling |
| 15-150 | `pair-03#2` | 15-150 | 15-213 | overview, worth, co_scheduling |
| 15-150 | `pair-07#0` | 15-150 | 15-213 | workload, difficulty_type, structure |
| 15-150 | `pair-02#0` | 15-150 | 15-122, 15-213, 15-251 | comparisons, co_scheduling |
| 15-150 | `pair-08#1` | 15-150 | 15-213, 15-251 | co_scheduling |
| 15-150 | `pair-04#0` | 15-150 | 15-210, 15-213 | co_scheduling |
| 15-213 | `reddit-15213-1hmut34-variousjob#0` | 15-213 | 15-122 | overview, workload, difficulty_type, structure, worth |
| 15-213 | `bowad-15-213-5#1` | 15-213 | 15-150 | overview, workload, difficulty_type |
| 15-251 | `abigalekim-15-251-16#0` | 15-251 | 15-150 | overview, workload, difficulty_type, structure |
| ml-4way | `reddit-10301-y9ha1g-mavaa#0` | 10-301 | 15-122 | overview, workload, structure, best_fit |
| ml-4way | `reddit-10301-1icft4q-acceptablespite#0` | 10-301 | 15-122 | overview, workload, structure, best_fit |
| ml-4way | `reddit-10301-y9ha1g-emoney#0` | 10-301 | 15-122 | workload, difficulty_type |
| ml-4way | `reddit-10601-1l213wr-moraceae#0` | 10-601 | 10-606, 10-607 | difficulty_type, best_fit |
| ml-4way | `reddit-10315-gpswxk-oppossum#1` | 10-315 | 15-213 | structure |

**14 rows.**

