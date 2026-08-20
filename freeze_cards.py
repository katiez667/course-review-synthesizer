"""freeze_cards.py — run the demo cards through the GATED synthesize() and save each
as static JSON in demo_data/.

Every answer here has passed audit_citations. Nothing is written for a card until all
of its facets pass; if the gate raises we stop the whole run and name the card+facet
rather than silently dropping it.

Retrieval is unchanged: recency=True is passed as a SOFT prior (mild age decay on the
similarity score), not a filter.
"""

import json, os, sys, time, datetime, traceback

import retrieval_spike as r
import synthesize as s
from synthesize import CitationAuditError

OUT = "demo_data"
K_SINGLE, K_MULTI = 5, 4
RECENCY = True

TITLES = {
    "15-150": "Principles of Functional Programming",
    "15-213": "Introduction to Computer Systems",
    "15-251": "Great Ideas in Theoretical Computer Science",
    "15-410": "Operating System Design and Implementation",
    "15-451": "Algorithm Design and Analysis",
    "85-102": "Introduction to Psychology",
    "10-301": "Introduction to Machine Learning (undergrad)",
    "10-315": "Introduction to Machine Learning (SCS majors)",
    "10-601": "Introduction to Machine Learning (masters)",
    "10-701": "Introduction to Machine Learning (PhD)",
}

# ── facet queries ──────────────────────────────────────────────────────────────
# Facet keys/labels come from the 11-facet schema in pathfinders_project_knowledge.md §10.
# Trimmed to the four every card's evidence can support; 15-150 gets two more.
def base_facets(course):
    n = course.replace("-", "")
    return [
        ("workload", "Workload & time",
         f"how many hours a week does {course} take, and when does the workload spike?"),
        ("difficulty_type", "Difficulty type",
         f"is {course} conceptually hard or is it mostly grinding and volume of work?"),
        ("structure", "Course structure",
         f"how is {course} structured - lectures, assignments, exams, TAs and office hours?"),
        ("worth", "Worth it?",
         f"is {course} worth taking - what does it unlock and what is the payoff?"),
    ]

EXTRA_15150 = [
    ("comparisons", "vs. other courses",
     "how does 15-150 compare to 15-122 and 15-112 in difficulty and style?"),
    ("co_scheduling", "Taking it with...",
     "can I take 15-150 and 15-213 together, or 15-150 and 15-251? what pairs badly?"),
]

SINGLE_CARDS = [
    ("15-150", "is 15-150 hard, how much work is it, and who should I take it with?"),
    ("15-213", "how hard is 15-213, what is the workload, and is it worth it?"),
    ("15-251", "how hard is 15-251, what is the workload, and is it worth it?"),
    ("15-410", "how hard is 15-410, what is the workload, and is it worth it?"),
    ("15-451", "how hard is 15-451, what is the workload, and is it worth it?"),
    ("85-102", "how hard is 85-102, what is the workload, and is it worth it?"),
]

ML_COURSES = ["10-301", "10-315", "10-601", "10-701"]
ML_OVERVIEW = ("I need one intro ML course. How do 10-301, 10-315, 10-601 and 10-701 "
               "differ in difficulty, math background, and who each one is for?")
ML_FACETS = [
    ("workload", "Workload & time",
     "how do the workloads of 10-301, 10-315, 10-601 and 10-701 compare week to week?"),
    ("difficulty_type", "Difficulty type",
     "how much math and theory does each of 10-301, 10-315, 10-601, 10-701 assume?"),
    ("structure", "Course structure",
     "how are 10-301, 10-315, 10-601 and 10-701 structured - homeworks, exams, projects?"),
    ("best_fit", "Who each is for",
     "which of 10-301, 10-315, 10-601, 10-701 should an undergrad vs masters vs PhD take?"),
]

# ── passage index: lets us build rich receipts without changing synthesize._pack ─
PASSAGE_BY_PID = {p["pid"]: p for p in r.PASSAGES}

def verdict_for(stats):
    """seek_out (green) vs avoid (rust). Computed once at freeze time and stored;
    the UI never recomputes it."""
    q, w = stats.get("quality"), stats.get("would_take_again_pct")
    if q is None or w is None:
        return "unknown"
    return "seek_out" if (q >= 3.5 and w >= 50) else "avoid"

def receipt(pid, packed):
    p = PASSAGE_BY_PID.get(pid, {})
    return {
        "id": pid,
        "text": packed["text"],
        "source": p.get("source"),
        "cite": packed["cite"],
        "url": packed["url"],
        "date": packed["date"],
        "verified": packed["verified"],
        "course": p.get("course"),
        "professor": p.get("professor"),
        "thread": p.get("thread"),
        "author": p.get("author"),
        "score": packed["score"],
    }

def harvest(bundle, receipts):
    """Fold every packed chunk in a bundle into the card-level receipts pool."""
    def walk(node):
        for pr in node.get("professors", {}).values():
            for c in pr["chunks"]:
                receipts.setdefault(c["id"], receipt(c["id"], c))
        for c in node.get("general", []):
            receipts.setdefault(c["id"], receipt(c["id"], c))
    walk(bundle)
    for sub in bundle.get("courses", {}).values():
        walk(sub)

def source_mix(receipts, ids=None):
    pool = [v for k, v in receipts.items() if ids is None or k in ids]
    mix = {"reddit": 0, "rmp": 0, "blog": 0}
    for x in pool:
        if x["source"] in mix:
            mix[x["source"]] += 1
    mix["total"] = len(pool)
    mix["verified"] = sum(1 for x in pool if x["verified"])
    mix["unverified"] = mix["total"] - mix["verified"]
    return mix

def run(label, bundle):
    """One gated call. Raises CitationAuditError -> caller stops the run."""
    t0 = time.time()
    answer = s.synthesize(bundle, verbose=True)
    cited, invented = s.audit_citations(answer, bundle)
    print(f"    {label}: {len(answer)} chars, {len(cited)} cited, {time.time()-t0:.0f}s",
          flush=True)
    return answer, cited

def prof_split(bundle_professors, course):
    if not bundle_professors:
        return {"available": False,
                "reason": "no per-instructor RMP stats for this course in the corpus",
                "professors": []}
    out = []
    for name, d in bundle_professors.items():
        st = r.PROFESSOR_STATS.get(name, {})
        out.append({
            "name": name,
            "verdict": verdict_for(st),
            "stats": st,
            "stats_line": d["stats"],
            "receipt_ids": [c["id"] for c in d["chunks"]],
        })
    return {"available": True, "reason": None, "professors": out}

def cross_course(cited_ids, course):
    rows = []
    for pid in sorted(cited_ids):
        cc = PASSAGE_BY_PID.get(pid, {}).get("course")
        if cc and cc != course:
            rows.append({"id": pid, "chunk_course": cc})
    return rows

def freeze_single(course, overview_q):
    facets_spec = base_facets(course) + (EXTRA_15150 if course == "15-150" else [])
    print(f"\n=== {course} ({1 + len(facets_spec)} calls) ===", flush=True)
    receipts, all_cited = {}, set()

    b = s.get_bundle(overview_q, course=course, k=K_SINGLE, recency=RECENCY)
    harvest(b, receipts)
    ans, cited = run("overview", b)
    all_cited |= set(cited)
    headline = {"question": overview_q, "answer_md": ans, "cited_ids": cited}
    split = prof_split(b["professors"], course)

    facets = []
    for key, label, q in facets_spec:
        fb = s.get_bundle(q, course=course, k=K_SINGLE, recency=RECENCY)
        harvest(fb, receipts)
        fa, fc = run(key, fb)
        all_cited |= set(fc)
        facets.append({"key": key, "label": label, "question": q,
                       "answer_md": fa, "cited_ids": fc})

    return {
        "card_id": course, "kind": "single", "course": course,
        "title": TITLES.get(course),
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
                      .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model": s.MODEL,
        "retrieval": {"k": K_SINGLE, "recency": RECENCY, "mode": "semantic"},
        "headline": headline,
        "facets": facets,
        "professor_split": split,
        "receipts": receipts,
        "source_mix": source_mix(receipts),
        "cross_course_citations": cross_course(all_cited, course),
    }

def freeze_multi():
    print(f"\n=== ml-4way ({1 + len(ML_FACETS)} calls) ===", flush=True)
    receipts, all_cited = {}, set()

    b = s.get_multi_bundle(ML_OVERVIEW, ML_COURSES, k=K_MULTI, recency=RECENCY)
    harvest(b, receipts)
    ans, cited = run("overview", b)
    all_cited |= set(cited)

    per_course = {}
    for c, sub in b["courses"].items():
        ids = {x["id"] for x in sub["general"]}
        for pr in sub["professors"].values():
            ids |= {x["id"] for x in pr["chunks"]}
        per_course[c] = {
            "title": TITLES.get(c),
            "professor_split": prof_split(sub["professors"], c),
            "receipt_ids": sorted(ids),
            "source_mix": source_mix(receipts, ids),
        }

    facets = []
    for key, label, q in ML_FACETS:
        fb = s.get_multi_bundle(q, ML_COURSES, k=K_MULTI, recency=RECENCY)
        harvest(fb, receipts)
        fa, fc = run(key, fb)
        all_cited |= set(fc)
        facets.append({"key": key, "label": label, "question": q,
                       "answer_md": fa, "cited_ids": fc})

    # every cited chunk's course vs the four the card is ABOUT
    cross = [{"id": pid, "chunk_course": PASSAGE_BY_PID.get(pid, {}).get("course")}
             for pid in sorted(all_cited)
             if PASSAGE_BY_PID.get(pid, {}).get("course") not in ML_COURSES]

    return {
        "card_id": "ml-4way", "kind": "multi", "courses": ML_COURSES,
        "title": "Which intro ML course?",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
                      .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model": s.MODEL,
        "retrieval": {"k": K_MULTI, "recency": RECENCY, "mode": "semantic"},
        "headline": {"question": ML_OVERVIEW, "answer_md": ans, "cited_ids": cited},
        "facets": facets,
        "per_course": per_course,
        "receipts": receipts,
        "source_mix": source_mix(receipts),
        "cross_course_citations": cross,
    }

def main():
    os.makedirs(OUT, exist_ok=True)
    written = []
    try:
        for course, q in SINGLE_CARDS:
            card = freeze_single(course, q)
            path = os.path.join(OUT, f"{course}.json")
            json.dump(card, open(path, "w"), indent=2, ensure_ascii=False)
            written.append(path)
            print(f"  -> wrote {path}", flush=True)

        card = freeze_multi()
        path = os.path.join(OUT, "ml-4way.json")
        json.dump(card, open(path, "w"), indent=2, ensure_ascii=False)
        written.append(path)
        print(f"  -> wrote {path}", flush=True)

    except CitationAuditError as e:
        print("\n" + "!" * 70, flush=True)
        print("GATE FAILED - run stopped. Nothing was silently dropped.", flush=True)
        print(f"  invented ids: {e.invented}", flush=True)
        print(f"  attempts: {e.attempts}", flush=True)
        print(f"  cards written before the failure: {written}", flush=True)
        traceback.print_exc()
        sys.exit(2)

    print(f"\nfroze {len(written)} cards:")
    for p in written:
        print("  ", p)

if __name__ == "__main__":
    main()
