"""
blog_ingest.py — build a course-review corpus from the CMU student-blog network.

Four stages:
  1. DISCOVER  — the set of course-review blogs (seed list + cross-links).
  2. FETCH     — pull each static page (no API, no auth, polite + cached).
  3. EXTRACT   — turn each heterogeneous page into per-course review chunks.
                 LLM extraction is the real path; a heuristic fallback runs with no key.
  4. NORMALIZE — emit chunks in the SAME schema your retrieval harness already uses,
                 with a new `course` field (blogs are multi-course, so retrieval must
                 filter by course).

This is a ONE-TIME pass for your demo course set — run it, cache the JSON, done.
"""

import os, re, json, time, html

# ── 1. DISCOVER ───────────────────────────────────────────────────────────────
# Known CMU course-review blogs (cross-linked from abigalekim.github.io/courses/
# and the cmu webring). Expand by following each page's outbound links.
SEEDS = [
    ("Abigale Kim",  "https://abigalekim.github.io/courses/"),
    ("Wan Shen Lim", "https://wanshenl.me/courses/"),
    ("Frank Fan",    "https://weihang7.github.io/courses/"),
    ("Fan Pu Zeng",  "https://fanpu.io/courses/"),
    ("Rui Ran",      "https://ruiran.me/courses/"),
    ("bokken12",     "https://bokken12.github.io/reviews/"),
    ("Pranav Kumar", "https://pranavkumar.me/courses/"),
    ("bowad",        "https://bowad.net/courses/"),
    ("schlomer",     "https://schlomer.xyz/cmu-courses/"),
    ("Joe McLaughlin","https://jmmclaug201.github.io/cmu-course-reviews/"),
]

CACHE = "blog_cache"

# ── 2. FETCH (runs in YOUR env; sandbox network is restricted) ────────────────
def fetch(url):
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_") + ".html")
    if os.path.exists(key):
        return open(key, encoding="utf-8").read()
    import requests  # pip install requests
    r = requests.get(url, headers={"User-Agent": "cmu-course-helper/0.1 (student project)"}, timeout=20)
    r.raise_for_status()
    open(key, "w", encoding="utf-8").write(r.text)
    time.sleep(1)  # be polite
    return r.text

def to_text(raw):
    """Strip HTML to readable text. bs4 if available, else a regex fallback."""
    try:
        from bs4 import BeautifulSoup  # pip install beautifulsoup4
        return BeautifulSoup(raw, "html.parser").get_text("\n")
    except Exception:
        t = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
        t = re.sub(r"(?s)<[^>]+>", "\n", t)
        return html.unescape(t)

# ── 3a. EXTRACT — LLM path (the real one) ─────────────────────────────────────
EXTRACT_PROMPT = """You are extracting course reviews from a CMU student's personal blog page.
Return ONLY a JSON array. For every course the student reviews, output one object:
  {"course": "15-150", "course_name": "<name or null>", "professor": "<name if stated, else null>",
   "date": "<semester/year if stated, else null>", "text": "<the student's actual words about THIS course, verbatim or lightly trimmed>"}
Rules: one object per course; if a paragraph covers several courses, split the sentences by which course they describe; never invent professors, dates, or opinions not in the text; skip courses only listed but not discussed. Output nothing but the JSON array.

PAGE TEXT:
---
{page}
---"""

def extract_llm(page_text, call_model):
    """call_model(prompt)->str is your model seam. Wire it to any API:
         Claude:  anthropic.Anthropic().messages.create(model=..., messages=[{"role":"user","content":prompt}])
         Gemini/Groq/Ollama: same idea, different client. All return a JSON string.
    """
    # 120k chars (~30k tokens) covers every seed page observed so far with headroom;
    # 12k was silently dropping ~85% of the largest page (fanpu.io, 80k chars).
    # .replace(), not .format(): the prompt's JSON example has literal {"course": ...}
    # braces that str.format() misreads as placeholders (KeyError: '"course"').
    raw = call_model(EXTRACT_PROMPT.replace("{page}", page_text[:120000]))
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    return json.loads(raw)

# ── 3b. EXTRACT — heuristic fallback (no key; rough, for smoke-testing) ────────
SEM = re.compile(r"^\s*#*\s*(Spring|Summer|Fall|Winter)\s+(\d{4})", re.I | re.M)
CODE = re.compile(r"\b(\d{2}-\d{3})\b")
PROF = re.compile(r"[Pp]rofessor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")

def extract_heuristic(page_text):
    # tag each line with the most recent semester header
    lines, cur, tagged = page_text.splitlines(), None, []
    for ln in lines:
        m = SEM.match(ln)
        if m:
            cur = f"{m.group(1).title()} {m.group(2)}"
        tagged.append((cur, ln))
    out = []
    # per-course bullet lines like "- 15-330: Relatively easy ... Bryan Parno ..."
    for sem, ln in tagged:
        m = CODE.search(ln)
        if m and len(ln.strip()) > 60:            # a real review line, not just a listing
            prof = PROF.search(ln)
            out.append({"course": m.group(1), "professor": prof.group(1) if prof else None,
                        "date": sem, "text": ln.strip(" -")})
    return out

# ── 4. NORMALIZE to your harness schema ───────────────────────────────────────
def slug(s): return re.sub(r"[^a-z0-9]+", "", s.lower())

def norm_course(code):
    """Model output is inconsistent (09222 vs 09-222) -> canonical NN-NNN."""
    digits = re.sub(r"\D", "", code)
    return f"{digits[:2]}-{digits[2:]}" if len(digits) >= 5 else code

def normalize(author, url, items):
    rows = []
    for i, it in enumerate(items):
        course = norm_course(it["course"])
        rows.append(dict(
            id=f"{slug(author)}-{course}-{i}",
            source="blog", author=author, url=url,
            course=course, professor=it.get("professor"),
            date=it.get("date"), text=it["text"],
        ))
    return rows

def build(use_llm=False, call_model=None):
    corpus = []
    for author, url in SEEDS:
        try:
            text = to_text(fetch(url))
        except Exception as e:
            print(f"skip {url}: {e}"); continue
        items = extract_llm(text, call_model) if use_llm else extract_heuristic(text)
        corpus += normalize(author, url, items)
        print(f"{author}: {len(items)} course chunks")
    json.dump(corpus, open("blog_corpus.json", "w"), indent=2, ensure_ascii=False)
    print(f"\nwrote blog_corpus.json ({len(corpus)} chunks)")
    return corpus


if __name__ == "__main__":
    # Demo: run the heuristic extractor on the real Abigale fixture (no network/key).
    text = open("abigale_fixture.txt", encoding="utf-8").read()
    rows = normalize("Abigale Kim", "https://abigalekim.github.io/courses/",
                     extract_heuristic(text))
    for r in rows:
        prof = f" prof={r['professor']}" if r["professor"] else ""
        print(f"[{r['course']}] {r['date']}{prof}\n    {r['text'][:150]}\n")
