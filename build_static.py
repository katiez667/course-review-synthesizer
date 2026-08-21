"""build_static.py — produce a dist/ that any static host can serve.

The demo's browse-only mode normally discovers cards by parsing a directory
listing, which python3 -m http.server provides and GitHub Pages / Netlify /
Vercel do not. This writes an explicit manifest.json instead, so the deployed
site needs no server at all.

Deliberately does NOT copy the raw corpus (blog_corpus.json, reddit_corpus.json,
rmp_corpus.json, corpus_15150.py). Only the cards ship, and a card contains just
the excerpts it actually cites, each with its source link. That is a much smaller
and more defensible public surface than republishing the whole scraped corpus.

    python3 build_static.py     ->  dist/
"""
import json, os, shutil

import corpus_all as c
from freeze_cards import TITLES

OUT = "dist"
SEED_DIR, CACHE_DIR = "demo_data", "card_cache"
ASSETS = ["preview.html", "CourseCard.jsx", "CourseCard.css"]


def card_rows():
    rows = []
    for d, origin in ((SEED_DIR, "seed"), (CACHE_DIR, "cache")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f.startswith("_"):
                continue
            j = json.load(open(os.path.join(d, f)))
            receipts = j.get("receipts", {})
            rows.append({
                "course": j.get("card_id"),
                "title": j.get("title"),
                "kind": j.get("kind", "single"),
                "member_courses": j.get("courses") or [],
                "origin": origin,
                "has_card": True,
                "receipts": len(receipts),
                "chunks": len(receipts),
                "sources": sorted({r.get("source") for r in receipts.values() if r.get("source")}),
                "hits": 0,
            })
    return rows


def corpus_rows(have):
    """Courses the corpus covers but that have no card — keeps the real coverage
    number honest on the deployed page."""
    counts = {}
    for x in c.CORPUS:
        if x["id"].endswith("-summary"):
            continue
        counts[x["course"]] = counts.get(x["course"], 0) + 1
    out = []
    for course, n in sorted(counts.items()):
        if course in have:
            continue
        out.append({"course": course, "title": TITLES.get(course), "chunks": n,
                    "receipts": None, "has_card": False, "origin": None,
                    "hits": 0, "kind": "single", "member_courses": []})
    return out


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for a in ASSETS:
        shutil.copy2(a, os.path.join(OUT, a))
    for d in (SEED_DIR, CACHE_DIR):
        if os.path.isdir(d):
            shutil.copytree(d, os.path.join(OUT, d),
                            ignore=shutil.ignore_patterns("_*"))

    cards = card_rows()
    have = {r["course"] for r in cards} | {m for r in cards for m in r["member_courses"]}
    rest = corpus_rows(have)
    courses = cards + rest

    manifest = {
        "courses": courses,
        "stats": {
            "cards_total": len(cards),
            "cards_seed": sum(1 for r in cards if r["origin"] == "seed"),
            "cards_cached": sum(1 for r in cards if r["origin"] == "cache"),
            # No live counters on a static host: nothing is being served or counted
            # here, so reporting cache hits would imply activity that isn't happening.
            "cache_hits": 0,
            "api_calls_spent": 0,
            "corpus_courses": len({r["course"] for r in courses}),
        },
        "has_key": False,
        "offline": True,
        "static_build": True,
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)

    total = sum(len(files) for _, _, files in os.walk(OUT))
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(OUT) for f in fs) / 1024
    print(f"dist/ built: {total} files, {size:.0f} KB")
    print(f"  cards: {len(cards)}  (seed {manifest['stats']['cards_seed']}, "
          f"cached {manifest['stats']['cards_cached']})")
    print(f"  courses listed: {len(courses)}")
    print(f"  NOT copied: raw corpus files, _meta.json, .env, server code")


if __name__ == "__main__":
    main()
