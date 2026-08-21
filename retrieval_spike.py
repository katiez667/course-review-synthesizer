"""
retrieval_spike.py  (v2) — cached-arm harness with the four spike fixes applied.

Fixes over v1, each targeting a diagnosed failure:
  1. SENTENCE-LEVEL CHUNKING  -> fixes take-01/take-05 dilution (T1, T5).
     Long multi-topic comments are split into short passages before embedding,
     so a single idea (e.g. "recursion = induction") isn't averaged into mud.
  2. STATS OUT OF EMBEDDINGS   -> fixes T2 "stats summary not retrieved".
     RMP summary stat blocks (4.1/5, 77% would-take-again, ...) are parsed into
     PROFESSOR_STATS and INJECTED on lookup, not embedded/retrieved.
  3. COURSE/THREAD SCOPING     -> fixes T3/T4 off-topic bleed.
     Comparison/co-scheduling queries filter to passages that actually mention
     the target course(s) before ranking, so 112-vs-122 chunks stop winning.
  4. RECENCY WEIGHTING         -> closes the T6 "unbuilt" gap.
     Similarity is multiplied by a mild age-decay weight when recency=True.

Retrieval mode: sentence-transformers if importable (what you ship), else TF-IDF.
Run:  python retrieval_spike.py
"""

import re
from corpus_all import CORPUS          # unified: 15-150 batch + blogs + RMP + Reddit

CURRENT_YEAR = 2026

# ---------- date -> year (Reddit relative "6y"/"9mo"; RMP absolute "2026-03") --
def parse_year(date):
    if not date:
        return None
    m = re.match(r"(\d{4})", date)
    if m:
        return int(m.group(1))
    # blog dates are season-prefixed ("Fall 2024"), so the leading-year match above
    # misses them and all 150 blog chunks used to fall through to the 0.85 fallback.
    m = re.search(r"(?:fall|spring|summer|winter)\s+(\d{4})", date, re.I)
    if m:
        return int(m.group(1))
    m = re.match(r"(\d+)\s*y", date)
    if m:
        return CURRENT_YEAR - int(m.group(1))
    m = re.match(r"(\d+)\s*mo", date)
    if m:
        return CURRENT_YEAR - (1 if int(m.group(1)) >= 6 else 0)
    return None

def recency_weight(year, half_life=5.0):
    if year is None:
        return 0.85
    age = max(0, CURRENT_YEAR - year)
    return 0.5 ** (age / half_life)

# ---------- FIX 2: pull structured stats out of the embedding corpus ----------
def parse_stats(text):
    q  = re.search(r"quality\s+(\d+(?:\.\d+)?)", text, re.I)
    wt = re.search(r"(\d+)%\s+would take again", text, re.I)
    d  = re.search(r"difficulty\s+(\d+(?:\.\d+)?)", text, re.I)
    return {
        "quality": float(q.group(1)) if q else None,
        "would_take_again_pct": int(wt.group(1)) if wt else None,
        "difficulty": float(d.group(1)) if d else None,
    }

PROFESSOR_STATS = {}
RAW = []
for c in CORPUS:
    if c["id"].endswith("-summary"):
        PROFESSOR_STATS[c["professor"]] = parse_stats(c["text"])
    else:
        RAW.append(c)

def stats_line(prof):
    s = PROFESSOR_STATS.get(prof)
    if not s:
        return f"{prof}: (no structured stats)"
    return (f"{prof}: quality {s['quality']}/5, "
            f"{s['would_take_again_pct']}% would take again, "
            f"difficulty {s['difficulty']}/5")

# ---------- FIX 1: sentence-level chunking ------------------------------------
def sentence_chunk(text, max_chars=240):
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    passages, cur = [], ""
    for s in sents:
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= max_chars:
            cur += " " + s
        else:
            passages.append(cur); cur = s
    if cur:
        passages.append(cur)
    return passages or [text]

PASSAGES = []
for c in RAW:
    for i, p in enumerate(sentence_chunk(c["text"])):
        PASSAGES.append({**c, "pid": f"{c['id']}#{i}", "year": parse_year(c["date"]), "passage": p})

# ---------- embedding (ship) / TF-IDF (fallback) ------------------------------
_ST_MODEL = None          # cache: the model was being rebuilt on every retrieve() call,
                          # which dominated runtime. Pure memoization — ranking is unchanged.
_ST_LOCK = __import__("threading").Lock()

def embed_texts(texts):
    """Thread-safe, CPU-pinned embedding.

    Two deliberate constraints, both learned from a hard crash:

    1. device="cpu". On Apple Silicon sentence-transformers auto-selects the MPS
       (Metal) backend. Concurrent encodes on MPS segfault the whole process inside
       at::native::mps::copy_cast_kernel_mps. This model is 22M params and the corpus
       is small, so CPU is fast enough and does not take the process down.
    2. A module-level lock. live_server.py is a ThreadingHTTPServer — one thread per
       request — and /api/ask embeds a query on every keystroke, so without this
       several encodes overlap. Serializing them costs milliseconds at this scale.

    Ranking is unaffected: same model, same weights, same normalized vectors.
    """
    global _ST_MODEL
    with _ST_LOCK:
        if _ST_MODEL is None:
            from sentence_transformers import SentenceTransformer
            _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return _ST_MODEL.encode(texts, normalize_embeddings=True)

def _semantic(query, docs):
    import numpy as np
    v = embed_texts(docs + [query]); return v[:-1] @ v[-1]

def _lexical(query, docs):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    M = TfidfVectorizer(stop_words="english").fit_transform(docs + [query])
    return cosine_similarity(M[-1], M[:-1]).ravel()

def _norm(a):
    import numpy as np
    a = np.asarray(a, float); lo, hi = a.min(), a.max()
    return (a - lo) / (hi - lo) if hi > lo else a * 0

# FIX 5: HYBRID retrieval. "takeaway"/"recursion" are strong LEXICAL signals the
# small embedding model dilutes; blending normalized semantic + lexical rescues them.
def _score(query, docs, mode="semantic", alpha=0.5):
    lex = _lexical(query, docs)
    try:
        sem = _semantic(query, docs)
    except Exception:
        return lex, "TF-IDF only (embeddings unavailable here)"
    if mode == "hybrid":
        return alpha * _norm(sem) + (1 - alpha) * _norm(lex), f"hybrid (alpha={alpha})"
    return sem, "semantic embeddings (all-MiniLM-L6-v2)"

# ---------- FIX 3 + 4: scoped, recency-weighted retrieval ---------------------
def retrieve(query, k=5, course=None, course_filter=None, thread_filter=None, professor=None, recency=False, mode="semantic"):
    pool = PASSAGES
    if professor:
        pool = [p for p in pool if p["professor"] == professor]
    if course:                                # FIX 3a: scope by the `course` METADATA field,
        pool = [p for p in pool if p["course"] == course]   # not by tokens in the passage text
    if thread_filter:                         # FIX 3b: scope to the RIGHT thread
        tf = thread_filter.lower()
        pool = [p for p in pool if tf in p["thread"].lower()]
    if course_filter:                         # token match on TEXT — for co-scheduling ("mentions 213")
        toks = [t.lower() for t in course_filter]
        pool = [p for p in pool
                if any(t in p["passage"].lower() or t in p["thread"].lower() for t in toks)]
    if not pool:
        return "n/a (empty pool)", []
    scores, smode = _score(query, [p["passage"] for p in pool], mode=mode)
    if recency:
        scores = [s * recency_weight(p["year"]) for s, p in zip(scores, pool)]
    order = sorted(range(len(pool)), key=lambda i: scores[i], reverse=True)[:k]
    return smode, [(pool[i], float(scores[i])) for i in order]

def rank_of(query, target_prefix, mode="semantic", **kw):
    """Where does a known-good chunk actually rank? Stops us guessing at top-5."""
    _, ranked = retrieve(query, k=len(PASSAGES), mode=mode, **kw)
    for i, (p, s) in enumerate(ranked, 1):
        if p["id"].startswith(target_prefix):
            return i, s, len(ranked)
    return None, None, len(ranked)

def show(label, hits):
    print(f"  {label}")
    for p, s in hits:
        pr = f" prof={p['professor']}" if p["professor"] else ""
        print(f"    [{s:.3f}] {p['pid']} ({p['source']} {p['date']}{pr})  {re.sub(r'\\s+',' ',p['passage'])[:120]}")

# ---------- test runner (scoping options mirror the fixes) --------------------
def main():
    print(f"corpus: {len(RAW)} comments -> {len(PASSAGES)} passages after sentence chunking")
    print(f"structured stats held out for: {', '.join(PROFESSOR_STATS)}\n")

    mode, hits = retrieve("Tell me about 15-150: workload difficulty what you learn is it worth it", 6)
    print("="*80); print(f"T1 facet coverage  [{mode}]"); show("top:", hits)

    print("="*80); print("T2 professor split  (grouped + injected stats)")
    for prof in ("Erdmann", "Brookes"):
        print(f"  >> {stats_line(prof)}")
        _, h = retrieve("is 15-150 hard, who should I take it with", 3, professor=prof)
        show(f"{prof} free-text:", h)

    print("="*80); print("T3 comparison  (thread_filter='15-122' + hybrid)")
    _, h = retrieve("15-150 vs 15-122 which is harder and more work", 5,
                    thread_filter="15-122", mode="hybrid"); show("top:", h)

    print("="*80); print("T4 co-scheduling  (course_filter=['213'])")
    _, h = retrieve("can I take 15-150 and 15-213 together", 5, course_filter=["213"]); show("top:", h)

    print("="*80); print("T5 signal vs noise  (hybrid)")
    q5 = "what do students take away from 15-150"
    _, h = retrieve(q5, 5, mode="hybrid"); show("top:", h)
    for tid in ("take-01", "take-05"):
        r, sc, n = rank_of(q5, tid, mode="hybrid")
        print(f"    rank probe: {tid} at #{r}/{n}")
    # FIX 6: query expansion — bridge the abstract query to concrete answer vocabulary
    q5x = (q5 + " such as recursion and induction proofs, functional programming "
                 "mindset, cleaner code, using map and reduce")
    print("  -- with query expansion (FIX 6) --")
    _, hx = retrieve(q5x, 5, mode="hybrid"); show("expanded:", hx)
    for tid in ("take-01", "take-05"):
        r, sc, n = rank_of(q5x, tid, mode="hybrid")
        print(f"    rank probe (expanded): {tid} at #{r}/{n}")

    print("="*80); print("T6 staleness  (recency=True)")
    _, h = retrieve("has 15-150 changed over the years, recent vs old reviews", 5, recency=True); show("top:", h)

def get_chunks_for_synthesis(query, k=4):
    """Return the evidence bundle for a professor-split query, ready to hand to Claude."""
    bundle = {"query": query, "professors": {}}
    for prof in PROFESSOR_STATS:                      # Erdmann, Brookes
        _, hits = retrieve(query, k=k, professor=prof)
        bundle["professors"][prof] = {
            "stats": stats_line(prof),                # the injected 4.1/77% line
            "chunks": [
                {"id": p["pid"], "date": p["date"], "text": p["passage"], "score": round(s, 3)}
                for p, s in hits
            ],
        }
    return bundle

import anthropic, json

def synthesize(bundle):
    evidence = json.dumps(bundle, indent=2, ensure_ascii=False)
    system = (
        "You answer course-selection questions using ONLY the provided evidence. "
        "Rules: (1) Never blend professors into one average — report each separately "
        "with their own stats and reviews. (2) Cite chunk ids in brackets, e.g. [rmp-brookes-01#0], "
        "for every claim. (3) If reviews conflict, surface the conflict rather than hiding it. "
        "(4) Note when evidence is old (dates are in the bundle). (5) End with a direct, "
        "actionable recommendation. Do not invent anything not in the evidence."
    )
    msg = anthropic.Anthropic().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content":
            f"Question: {bundle['query']}\n\nEvidence:\n{evidence}\n\n"
            "Write one grounded answer that keeps the professors distinct."}],
    )
    return msg.content[0].text

if __name__ == "__main__":
    b = get_chunks_for_synthesis("is 15-150 hard, who should I take it with")
    print(synthesize(b))
