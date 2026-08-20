"""live_compile_demo.py — the ONE part of this repo that is allowed to spend money.

Demonstrates the real pipeline end to end for a course that has never been frozen:
    raw corpus JSON  ->  retrieve()  ->  get_bundle() (provenance-packed)
    ->  synthesize() (gated: audit_citations, retry, cap 3)  ->  card-shaped JSON

This is a sibling of freeze_cards.py, not a replacement — freeze_cards.py batch-writes
all 7 demo_data/ cards (37 calls). This module compiles exactly ONE course, and by
default only the overview headline (1 call), so a single compile costs one gated call,
not five.

It writes to card_cache/, never to demo_data/, so the frozen preview is untouched
unless you explicitly copy the result over.

Importable by live_server.py (the browser-facing lab) as well as runnable directly:
    env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='sk-...' python3 live_compile_demo.py 15-440
    env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='sk-...' python3 live_compile_demo.py 15-440 --full
"""

import argparse, json, os, sys, time, datetime

import retrieval_spike as r
import synthesize as s
from synthesize import CitationAuditError
from freeze_cards import (
    TITLES, base_facets, harvest, receipt, source_mix, prof_split,
    cross_course, run as gated_run, PASSAGE_BY_PID,
)

OUT_DIR = "card_cache"


class NoEvidenceError(RuntimeError):
    """Raised instead of exiting the process — a long-running server must survive a
    course with zero corpus coverage, not just a CLI invocation."""


def overview_question(course):
    return f"how hard is {course}, what is the workload, and is it worth it?"


def retrieval_preview(course, question=None, k=5):
    """The free half: what retrieve() actually pulls, before any model call happens.
    Returns plain data (JSON-able) so both the CLI printer and the HTTP server can
    use it without duplicating the retrieve() call."""
    question = question or overview_question(course)
    mode, hits = r.retrieve(question, k=k, course=course, recency=True)
    return {
        "course": course,
        "question": question,
        "mode": mode,
        "hits": [
            {
                "pid": p["pid"], "source": p["source"], "professor": p.get("professor"),
                "date": p.get("date"), "score": round(float(sc), 3),
                "snippet": p["passage"][:180],
            }
            for p, sc in hits
        ],
    }


def show_retrieval(course, question, k):
    """CLI-only: print retrieval_preview()."""
    data = retrieval_preview(course, question, k)
    print(f"\n--- retrieval [{data['mode']}]: {len(data['hits'])} passages for {course!r} ---")
    for h in data["hits"]:
        prof = h["professor"] or "—"
        print(f"  [{h['score']:.3f}] {h['pid']:<28} {h['source']:<7} prof={prof:<20} "
              f"{h['snippet'][:70]!r}")
    if not data["hits"]:
        print("  (nothing retrieved — this course's corpus coverage is too thin)")
    return data["hits"]


def compile_card(course, full=False, k=5, verbose=True):
    """Runs 1 (or 5, if full) real gated API calls. Raises NoEvidenceError if the
    corpus has nothing for this course — caller decides how to surface that (CLI
    exits, the server turns it into a 422)."""
    title = TITLES.get(course, course)
    overview_q = overview_question(course)

    if verbose:
        print(f"\n=== live compile: {course} ({title}) ===")
        show_retrieval(course, overview_q, k)

    receipts, all_cited = {}, set()

    b = s.get_bundle(overview_q, course=course, k=k, recency=True)
    if not b.get("professors") and not b.get("general"):
        raise NoEvidenceError(f"no corpus evidence for {course!r}")

    harvest(b, receipts)
    ans, cited = gated_run("overview", b)
    all_cited |= set(cited)
    headline = {"question": overview_q, "answer_md": ans, "cited_ids": cited}
    split = prof_split(b["professors"], course)

    facets = []
    if full:
        for key, label, q in base_facets(course):
            fb = s.get_bundle(q, course=course, k=k, recency=True)
            harvest(fb, receipts)
            fa, fc = gated_run(key, fb)
            all_cited |= set(fc)
            facets.append({"key": key, "label": label, "question": q,
                           "answer_md": fa, "cited_ids": fc})

    return {
        "card_id": course, "kind": "single", "course": course,
        "title": title,
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
                      .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model": s.MODEL,
        "retrieval": {"k": k, "recency": True, "mode": "semantic", "live_demo": True},
        "headline": headline,
        "facets": facets,
        "professor_split": split,
        "receipts": receipts,
        "source_mix": source_mix(receipts),
        "cross_course_citations": cross_course(all_cited, course),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("course", help='course code, e.g. "15-440" (must exist in the corpus)')
    ap.add_argument("--full", action="store_true",
                     help="also run the 4 facet calls (5 gated calls total, not 1)")
    ap.add_argument("--k", type=int, default=5, help="retrieval top-k (default 5)")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set in this shell. This script makes a real, "
                 "billable API call and refuses to guess a key.")

    t0 = time.time()
    try:
        card = compile_card(args.course, full=args.full, k=args.k)
    except NoEvidenceError as e:
        sys.exit(f"\n{e} — nothing to synthesize. Stopping.")
    except CitationAuditError as e:
        print("\nGATE FAILED — a bad answer was caught and refused, not shown.")
        print(f"  invented ids: {e.invented}\n  attempts: {e.attempts}")
        sys.exit(2)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{args.course}.json")
    json.dump(card, open(path, "w"), indent=2, ensure_ascii=False)

    n_calls = 1 + (4 if args.full else 0)
    print(f"\n-> wrote {path}  ({n_calls} gated call{'s' if n_calls != 1 else ''}, "
          f"{time.time()-t0:.0f}s)")
    print(f"   {card['source_mix']['total']} receipts, "
          f"{card['source_mix']['verified']} verified, "
          f"{len(card['headline']['cited_ids'])} cited in the headline")
    print(f"\nView it: cp {path} demo_data/  (then reload preview.html — NOT done for you)")


if __name__ == "__main__":
    main()
