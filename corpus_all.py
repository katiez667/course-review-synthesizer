"""corpus_all.py — unify the 15-150 review corpus + the blog network into one list.

Every chunk ends up with the SAME keys so the retrieval harness treats them uniformly:
  id, source, course, thread, professor, date, role, author, url, text
Import CORPUS from here instead of from corpus_15150.
"""
import json
from corpus_15150 import CORPUS as C150

def _norm(c):
    return dict(
        id=c["id"], source=c.get("source"),
        course=c.get("course", "15-150"),                       # 15-150 corpus is all one course
        thread=c.get("thread") or f"blog · {c.get('author','')}",# blogs get a synthetic 'thread'
        professor=c.get("professor"), date=c.get("date"),
        role=c.get("role"), author=c.get("author"),
        url=c.get("url"), text=c["text"],
    )

CORPUS = [_norm(c) for c in C150]                                # Reddit + RMP (course=15-150)
try:
    CORPUS += [_norm(c) for c in json.load(open("blog_corpus.json"))]  # blog network (many courses)
except FileNotFoundError:
    pass
try:
    CORPUS += [_norm(c) for c in json.load(open("rmp_corpus.json"))]   # live RMP pull (many courses)
except FileNotFoundError:
    pass
try:
    CORPUS += [_norm(c) for c in json.load(open("reddit_corpus.json"))] # live Reddit pull (many courses)
except FileNotFoundError:
    pass


# Real RMP profile URLs (surfaced by the live-search arm). Reddit permalinks are
# intentionally NOT invented — hand-pasted chunks stay url=None until the API supplies one.
RMP_PROFILE = {
    "Erdmann": "https://www.ratemyprofessors.com/professor/2450311",
    "Brookes": "https://www.ratemyprofessors.com/professor/776856",
}

def _backfill_url(c):
    if c.get("url"):
        return c["url"]
    if c.get("source") == "rmp":
        return RMP_PROFILE.get(c.get("professor"))
    return None   # reddit hand-pasted: no verified link -> stays None on purpose

def provenance(c):
    """One uniform citation object for ANY chunk, regardless of source type."""
    src = c.get("source")
    url = _backfill_url(c)
    if src == "blog":
        label = f"{c.get('author','?')} \u2014 course reviews"
    elif src == "rmp":
        label = f"RateMyProfessors \u2014 {c.get('professor','?')}"
    elif src == "reddit":
        label = "r/cmu"
    else:
        label = src or "unknown"
    return {"source": src, "label": label, "url": url,
            "date": c.get("date"), "verified": bool(url)}

def cite(c):
    """Render a display citation: 'source \u00b7 date \u00b7 link' (or 'link pending' if unverified)."""
    p = provenance(c)
    tail = f" \u00b7 {p['date']}" if p["date"] else ""
    link = p["url"] if p["url"] else "link pending"
    return f"{p['label']}{tail} \u00b7 {link}"

if __name__ == "__main__":
    from collections import Counter
    print("total chunks:", len(CORPUS))
    print("by source:", dict(Counter(c["source"] for c in CORPUS)))
    print("courses covered:", sorted(set(c["course"] for c in CORPUS)))
