"""live_server.py — one server behind one unified demo surface.

There is no longer a "frozen demo" and a separate "live demo". There is ONE space:
a growing library of course cards. Some were compiled ahead of time (demo_data/,
the curated seed from freeze_cards.py); the rest accumulate in card_cache/ as people
search for them. To the user they are the same thing — cards that already exist and
cost nothing to open.

That IS the expansion model: a card is compiled at most once, ever. The first search
for a course pays one gated API call; every search after that is a cache hit at zero
cost. The counter on the landing page reports exactly that, so the saving is
measured rather than asserted.

Two card sources, deliberately kept separate on disk:
  demo_data/   seed cards, reproducible via freeze_cards.py, NEVER written at runtime
  card_cache/  everything compiled on demand, plus _meta.json (hits + timestamps)
Presented as one list. Split only so a runtime bug can't corrupt the curated set.

Endpoints:
    GET  /api/courses           every corpus course + whether a card already exists
    GET  /api/card?course=X     a card that already exists (counts a hit, never spends)
    GET  /api/ask?q=...         FREE — matches free text against already-answered
                                questions across the card library; no model call ever
    GET  /api/preview?course=X  FREE — the passages retrieval would use, no model call
    POST /api/compile           the ONLY billable path; explicit, one course at a time

Guardrails on /api/compile:
  - refuses unless ANTHROPIC_API_KEY is in the SERVER's env; never read from a client
  - the key never appears in a response, header, or log line
  - binds 127.0.0.1 only
  - validates corpus coverage before spending (NoEvidenceError -> 422)
  - won't recompile an existing card unless explicitly forced
  - a failed citation gate is surfaced, never swallowed

Run:
    env -u ANTHROPIC_BASE_URL ANTHROPIC_API_KEY='sk-...' python3 live_server.py
    then open http://localhost:8000/preview.html

Without a key: browsing every existing card still works; only compiling is disabled.
"""

import json, os, sys, traceback, datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import answer_index
import corpus_all as c
import live_compile_demo as live
from synthesize import CitationAuditError
from freeze_cards import TITLES

PORT = 8000
SEED_DIR = "demo_data"      # curated, read-only at runtime
CACHE_DIR = "card_cache"    # grows as courses are searched
META_FILE = os.path.join(CACHE_DIR, "_meta.json")


def has_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _load_meta():
    try:
        return json.load(open(META_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cards": {}, "api_calls_spent": 0, "cache_hits": 0}


def _save_meta(m):
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(m, open(META_FILE, "w"), indent=2)


def card_files():
    """Which cards exist, and where. Seed wins if a course somehow appears in both."""
    out = {}
    for d, origin in ((CACHE_DIR, "cache"), (SEED_DIR, "seed")):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".json") and not f.startswith("_"):
                out[f[:-5]] = {"origin": origin, "path": os.path.join(d, f), "dir": d}
    return out


def corpus_course_index():
    """Every course the corpus can support, joined against cards that already exist.
    Multi-course cards (ml-4way) are surfaced by their card id as well as their
    member courses, so searching '10-301' finds the comparison card that covers it."""
    counts, sources = {}, {}
    for x in c.CORPUS:
        if x["id"].endswith("-summary"):
            continue
        counts[x["course"]] = counts.get(x["course"], 0) + 1
        sources.setdefault(x["course"], set()).add(x["source"])

    cards, meta = card_files(), _load_meta()
    rows = []
    for course, n in sorted(counts.items()):
        card = cards.get(course)
        cmeta = meta["cards"].get(course, {})
        # `chunks` is corpus coverage (what COULD be retrieved); `receipts` is what the
        # built card actually cites. They differ — retrieval takes top-k, not everything —
        # so the UI must not label one as the other.
        receipts = None
        if card:
            try:
                receipts = len(json.load(open(card["path"])).get("receipts", {}))
            except (json.JSONDecodeError, OSError):
                pass
        rows.append({
            "course": course, "title": TITLES.get(course), "chunks": n,
            "receipts": receipts,
            "sources": sorted(sources.get(course, [])),
            "has_card": bool(card),
            "origin": card["origin"] if card else None,
            "hits": cmeta.get("hits", 0),
            "compiled_at": cmeta.get("compiled_at"),
        })

    # cards that aren't a single corpus course (e.g. the ml-4way comparison card)
    seen = {r["course"] for r in rows}
    for cid, card in sorted(cards.items()):
        if cid in seen:
            continue
        try:
            j = json.load(open(card["path"]))
        except (json.JSONDecodeError, OSError):
            continue
        rows.append({
            "course": cid, "title": j.get("title"),
            "chunks": len(j.get("receipts", {})),
            "receipts": len(j.get("receipts", {})),
            "sources": sorted({r.get("source") for r in j.get("receipts", {}).values() if r.get("source")}),
            "has_card": True, "origin": card["origin"],
            "hits": meta["cards"].get(cid, {}).get("hits", 0),
            "compiled_at": meta["cards"].get(cid, {}).get("compiled_at"),
            "member_courses": j.get("courses") or [],
            "kind": j.get("kind", "single"),
        })
    return rows


def library_stats():
    cards, meta = card_files(), _load_meta()
    return {
        "cards_total": len(cards),
        "cards_seed": sum(1 for v in cards.values() if v["origin"] == "seed"),
        "cards_cached": sum(1 for v in cards.values() if v["origin"] == "cache"),
        "cache_hits": meta.get("cache_hits", 0),
        "api_calls_spent": meta.get("api_calls_spent", 0),
    }


class Handler(SimpleHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Static assets must always revalidate. SimpleHTTPRequestHandler only sends
        # Last-Modified, so a browser will happily reuse a stale preview.html and
        # silently hide newly added features — the worst way to find out mid-demo.
        # (JSON responses set their own no-store in _json and skip this.)
        if getattr(self, "_no_cache_static", False):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/api/courses":
            return self._json(200, {
                "courses": corpus_course_index(),
                "stats": library_stats(),
                "has_key": has_key(),
            })

        if parsed.path == "/api/card":
            course = (qs.get("course") or [""])[0].strip()
            card = card_files().get(course)
            if not card:
                return self._json(404, {"error": f"no card for {course!r} yet",
                                         "needs_compile": True})
            meta = _load_meta()
            entry = meta["cards"].setdefault(course, {})
            entry["hits"] = entry.get("hits", 0) + 1
            meta["cache_hits"] = meta.get("cache_hits", 0) + 1
            _save_meta(meta)
            payload = json.load(open(card["path"]))
            payload["_origin"] = card["origin"]
            payload["_hits"] = entry["hits"]
            return self._json(200, payload)

        if parsed.path == "/api/ask":
            q = (qs.get("q") or [""])[0].strip()
            if not q:
                return self._json(400, {"error": "missing ?q="})
            return self._json(200, answer_index.ask(q))

        if parsed.path == "/api/preview":
            course = (qs.get("course") or [""])[0].strip()
            if not course:
                return self._json(400, {"error": "missing ?course="})
            if course not in {r["course"] for r in corpus_course_index()}:
                return self._json(404, {"error": f"{course!r} has no chunks in the corpus"})
            return self._json(200, live.retrieval_preview(course))

        # Static serving is rooted at the project dir, which also contains .env and
        # .claude/settings.local.json. SimpleHTTPRequestHandler would happily serve
        # both. Bound to localhost or not, credentials must never be fetchable over
        # HTTP — any local process (or a tunnel someone opens later) could read them.
        if self._is_blocked(parsed.path):
            return self._json(404, {"error": "not found"})

        self._no_cache_static = True
        return super().do_GET()

    BLOCKED_NAMES = {"settings.local.json"}

    @staticmethod
    def _is_blocked(path):
        from urllib.parse import unquote
        parts = [seg for seg in unquote(path).split("/") if seg]
        # any dotfile/dotdir (.env, .git, .claude, ...) plus explicit denies
        return any(seg.startswith(".") for seg in parts) or \
               any(seg in Handler.BLOCKED_NAMES for seg in parts)

    def do_POST(self):
        if urlparse(self.path).path != "/api/compile":
            return self._json(404, {"error": "not found"})

        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0) or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "malformed JSON body"})

        course = str(body.get("course", "")).strip()
        full, force = bool(body.get("full")), bool(body.get("force"))

        if course not in {r["course"] for r in corpus_course_index()}:
            return self._json(400, {"error": f"{course!r} has no chunks in the corpus"})

        # Existing card short-circuits before the key check: opening what's already
        # been compiled is free and must work with no key configured at all.
        existing = card_files().get(course)
        if existing and not force:
            cached = json.load(open(existing["path"]))
            if (not full) or len(cached.get("facets", [])) > 0:
                cached["_cached"] = True
                cached["_origin"] = existing["origin"]
                return self._json(200, cached)

        if existing and existing["origin"] == "seed" and force:
            return self._json(409, {"error": "refusing to overwrite a curated seed card "
                                              "from demo_data/. Re-freeze it with "
                                              "freeze_cards.py if that's really intended."})

        if not has_key():
            return self._json(503, {"error": "ANTHROPIC_API_KEY is not set on the server. "
                                              "Restart live_server.py with the key exported "
                                              "in its shell — the browser cannot supply it."})

        print(f"[compile] {course} full={full} force={force}", file=sys.stderr)
        try:
            card = live.compile_card(course, full=full, k=5)
        except live.NoEvidenceError as e:
            return self._json(422, {"error": str(e)})
        except CitationAuditError as e:
            return self._json(502, {"error": "citation gate failed after retries — refused "
                                              "rather than showing an ungrounded answer",
                                     "invented": sorted(e.invented), "attempts": e.attempts})
        except Exception as e:
            traceback.print_exc()
            return self._json(500, {"error": f"{type(e).__name__}: {e}"})

        os.makedirs(CACHE_DIR, exist_ok=True)
        json.dump(card, open(os.path.join(CACHE_DIR, f"{course}.json"), "w"),
                  indent=2, ensure_ascii=False)

        n_calls = 1 + (4 if full else 0)
        meta = _load_meta()
        meta["cards"][course] = {
            "hits": meta["cards"].get(course, {}).get("hits", 0),
            "compiled_at": datetime.datetime.now(datetime.timezone.utc)
                            .isoformat(timespec="seconds").replace("+00:00", "Z"),
            "calls": n_calls,
        }
        meta["api_calls_spent"] = meta.get("api_calls_spent", 0) + n_calls
        _save_meta(meta)

        answer_index.build(force=True)   # the new card is immediately askable
        card["_cached"] = False
        card["_origin"] = "cache"
        return self._json(200, card)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")


def main():
    if not has_key():
        print("WARNING: ANTHROPIC_API_KEY not set — browsing works, compiling returns 503.\n",
              file=sys.stderr)
    base = os.environ.get("ANTHROPIC_BASE_URL")
    if base and "api.anthropic.com" not in base:
        print(f"WARNING: ANTHROPIC_BASE_URL={base} may reject a normal key. Unset it if "
              "compiles fail.\n", file=sys.stderr)
    s = library_stats()
    print(f"card library: {s['cards_total']} cards "
          f"({s['cards_seed']} seed + {s['cards_cached']} cached)")
    print(f"unified demo:  http://127.0.0.1:{PORT}/preview.html  (localhost only)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
