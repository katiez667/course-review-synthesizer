"""answer_index.py — free-text questions answered WITHOUT a model call.

Every compiled card already stores, per tab, the exact question it answers plus a
gated, cited answer. Across the card library that's a few dozen pre-answered
questions. This module embeds those question strings once and matches a user's
free text against them, so "how much time does 150 eat" lands on 15-150's stored
workload answer instantly, at zero cost.

This is retrieval over cached ANSWERS, not new synthesis. It never calls Claude.
When nothing matches well it says so and hands the caller a compile suggestion
rather than returning a weak match dressed up as an answer — the same fail-closed
instinct as the citation gate.

Scoring:
  - cosine similarity (embed_texts returns normalized vectors, so a dot product is
    the cosine) between the query and each stored question
  - an explicit course code in the query is treated as a HARD filter when a card for
    it exists: "is 15-213 hard" must not answer from the 15-150 card
"""

import json, os, re

from retrieval_spike import embed_texts

SEED_DIR = "demo_data"
CACHE_DIR = "card_cache"

# below this cosine, we refuse to call it an answer
MATCH_THRESHOLD = 0.45

COURSE_RE = re.compile(r"\b(\d{2})\s*-?\s*(\d{3})\b")

_INDEX = None       # [{...entry...}]
_VECS = None        # embedding matrix aligned with _INDEX
_SIG = None         # (path, mtime) signature the index was built from


def course_codes(text):
    """Course codes a user might type: '15213', '15-213', '15 213' -> '15-213'."""
    return [f"{a}-{b}" for a, b in COURSE_RE.findall(text or "")]


def _signature():
    sig = []
    for d in (SEED_DIR, CACHE_DIR):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".json") and not f.startswith("_"):
                p = os.path.join(d, f)
                sig.append((p, os.path.getmtime(p)))
    return tuple(sig)


def _entries():
    """One entry per answerable tab across every card that exists."""
    out = []
    for d, origin in ((SEED_DIR, "seed"), (CACHE_DIR, "cache")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f.startswith("_"):
                continue
            try:
                card = json.load(open(os.path.join(d, f)))
            except (json.JSONDecodeError, OSError):
                continue
            courses = card.get("courses") or [card.get("course")]
            courses = [c for c in courses if c]
            tabs = [("overview", "Overview", card.get("headline") or {})]
            tabs += [(fa.get("key"), fa.get("label"), fa) for fa in card.get("facets", [])]
            for key, label, node in tabs:
                q = node.get("question")
                if not q or not node.get("answer_md"):
                    continue
                out.append({
                    "card_id": card.get("card_id"), "origin": origin,
                    "course": card.get("course"), "courses": courses,
                    "title": card.get("title"), "kind": card.get("kind", "single"),
                    "tab_key": key, "tab_label": label, "question": q,
                    "answer_md": node["answer_md"],
                    "cited_ids": node.get("cited_ids", []),
                    "_receipts": card.get("receipts", {}),
                })
    return out


def build(force=False):
    """Rebuild only when the set of card files (or their mtimes) actually changed,
    so a newly compiled card becomes askable immediately without re-embedding on
    every request."""
    global _INDEX, _VECS, _SIG
    sig = _signature()
    if not force and _INDEX is not None and sig == _SIG:
        return _INDEX
    entries = _entries()
    _INDEX = entries
    _SIG = sig
    # Embed question + course + title: the facet questions are formulaic, so without
    # the title "how long does functional programming take" matches whichever course
    # happens to phrase its workload question closest, not 15-150.
    _VECS = embed_texts([
        " ".join(filter(None, [e["question"], " ".join(e["courses"] or []), e["title"]]))
        for e in entries
    ]) if entries else None
    return _INDEX


def ask(query, k=4):
    """Rank stored answers against free text. Never calls a model."""
    build()
    if not _INDEX:
        return {"query": query, "good_match": False, "matches": [],
                "reason": "no cards compiled yet", "compile_hint": None}

    import numpy as np
    qv = embed_texts([query])[0]
    scores = (_VECS @ qv).tolist()

    named = course_codes(query)
    pool = list(range(len(_INDEX)))
    filtered_to = None
    named_uncovered = False
    if named:
        # a named course that HAS a card constrains the answer to that card
        hits = [i for i in pool
                if any(c in named for c in (_INDEX[i]["courses"] or []))]
        if hits:
            pool = hits
            filtered_to = named
        else:
            # user asked about a specific course we have no card for. Anything we
            # returned would be about some OTHER course, so refuse to call it a match.
            named_uncovered = True

    ranked = sorted(pool, key=lambda i: scores[i], reverse=True)[:k]
    best = scores[ranked[0]] if ranked else -1.0

    # a course the user named that we have no card for -> offer to compile it
    have = {c for e in _INDEX for c in (e["courses"] or [])}
    compile_hint = next((c for c in named if c not in have), None)

    matches = []
    for rank, i in enumerate(ranked):
        e = _INDEX[i]
        m = {
            "card_id": e["card_id"], "course": e["course"], "courses": e["courses"],
            "title": e["title"], "kind": e["kind"], "origin": e["origin"],
            "tab_key": e["tab_key"], "tab_label": e["tab_label"],
            "question": e["question"], "score": round(float(scores[i]), 3),
        }
        if rank == 0:      # only the top match carries the full answer payload
            cited = [c for c in e["cited_ids"] if c in e["_receipts"]]
            m["answer_md"] = e["answer_md"]
            m["cited_ids"] = cited
            m["receipts"] = {c: e["_receipts"][c] for c in cited}
        matches.append(m)

    return {
        "query": query,
        "good_match": (bool(matches) and best >= MATCH_THRESHOLD
                        and not named_uncovered),
        "named_uncovered": named_uncovered,
        "best_score": round(float(best), 3),
        "threshold": MATCH_THRESHOLD,
        "scoped_to": filtered_to,
        "compile_hint": compile_hint,
        "matches": matches,
    }


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "is 15-150 hard"
    r = ask(q)
    print(f"query: {r['query']!r}  best={r['best_score']}  good={r['good_match']}"
          f"  scoped={r['scoped_to']}  compile_hint={r['compile_hint']}")
    for m in r["matches"]:
        print(f"  [{m['score']:.3f}] {m['card_id']:<9} {m['tab_label']:<18} {m['question'][:70]}")
