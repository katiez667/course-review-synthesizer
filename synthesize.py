"""
synthesize.py — turn retrieved chunks into ONE grounded answer whose every claim
carries a real, source-linked citation.

Key property: provenance flows all the way through. Each chunk handed to the model
already includes its {label, url, date, verified}, and the prompt forbids citing
anything not in the evidence — so the model can't invent a source, and unverified
chunks (no fetched URL) are marked as such rather than dressed up with a fake link.
"""

import json
from retrieval_spike import retrieve, PROFESSOR_STATS, stats_line
from corpus_all import provenance

# ── build the evidence bundle (professor-split shape; provenance attached) ──────
def get_bundle(query, course="15-150", k=4, recency=False):
    bundle = {"query": query, "course": course, "professors": {}, "general": []}
    profs = [p for p in PROFESSOR_STATS]                      # Erdmann, Brookes (have RMP stats)
    if profs:
        for prof in profs:
            _, hits = retrieve(query, k=k, course=course, professor=prof, recency=recency)
            if not hits:          # prof has no evidence for THIS course -> omit entirely.
                continue          # keeps 15-150 stats out of a 10-301 bundle (invariant 1).
            bundle["professors"][prof] = {
                "stats": stats_line(prof),
                "chunks": [_pack(p, s) for p, s in hits],
            }
    # course-level chunks not tied to a professor (blogs, general Reddit)
    _, gen = retrieve(query, k=k, course=course, recency=recency)
    seen = {c["id"] for pr in bundle["professors"].values() for c in pr["chunks"]}
    bundle["general"] = [_pack(p, s) for p, s in gen if p["pid"] not in seen]
    return bundle

def _pack(p, score):
    prov = provenance(p)
    return {"id": p["pid"], "text": p["passage"], "score": round(score, 3),
            "cite": prov["label"], "url": prov["url"], "date": prov["date"],
            "verified": prov["verified"]}

# ── synthesis prompt: provenance required, evidence-only ───────────────────────
SYSTEM = (
    "You answer a student's course question using ONLY the evidence provided. Rules:\n"
    "1. Never blend professors into one average — report each separately with their own stats.\n"
    "2. Every claim ends with a citation drawn from the chunk's own fields, formatted "
    "   [id \u00b7 cite \u00b7 date \u00b7 url] — id is the chunk's own \"id\" field, "
    "   copied EXACTLY, so every citation is mechanically traceable back to the "
    "   evidence. If the chunk is unverified (url is null), write "
    "   [id \u00b7 cite \u00b7 date \u00b7 link pending] — never invent a URL.\n"
    "3. Only cite chunks present in the evidence. Never introduce a source that isn't there.\n"
    "4. Surface conflicts; note when evidence is old; end with a direct recommendation.\n"
    "5. Show the source mix (blog / Reddit / RMP) so the reader can weigh it.\n"
    "6. When the evidence contains a first-person account of struggling, or a clear "
    "   dissent from the majority view, QUOTE IT DIRECTLY rather than summarizing it. "
    "   The raw student voice is the point — do not soften it into an abstraction.\n"
    "7. Reproduce quoted text VERBATIM: exact capitalization, spelling, and punctuation "
    "   as it appears in the chunk. Never place markdown (**bold**, *italics*) inside "
    "   quotation marks, and never re-capitalize a quoted word."
)

# ── failure mode: synthesis cited something that isn't in the evidence ──────────
class CitationAuditError(RuntimeError):
    """Raised when synthesis keeps inventing citations. Fail closed — never display."""
    def __init__(self, attempts, invented, answer):
        self.attempts, self.invented, self.answer = attempts, invented, answer
        super().__init__(
            f"citation audit failed after {attempts} attempt(s); "
            f"invented ids still present: {invented}"
        )

CORRECTION = (
    "\n\n--- CORRECTION (attempt {n}) ---\n"
    "Your previous answer cited these ids, which are NOT in the evidence above: {bad}\n"
    "Those chunks do not exist in this bundle. You may have inferred them from the "
    "id naming pattern — that is fabrication, even if such a chunk exists elsewhere.\n"
    "The ONLY ids you may cite are:\n{valid}\n"
    "Rewrite the full answer, citing exclusively from that list."
)

def _user_msg(bundle):
    course = bundle.get("course") or ", ".join(bundle.get("courses", {}))
    return (f"Question: {bundle['query']}\nCourse: {course}\n\n"
            f"Evidence (JSON):\n{json.dumps(bundle, indent=2, ensure_ascii=False)}\n\n"
            "Write one grounded answer following the rules.")

def synthesize_once(bundle, call_model=None):
    """Raw, ungated single call. Use synthesize() unless you're debugging."""
    return (call_model or claude)(SYSTEM, _user_msg(bundle))

def synthesize(bundle, call_model=None, max_attempts=3, verbose=False):
    """Gated synthesis. Every cited id must be in the bundle, or we retry, then fail closed.

    The ONLY check is id-in-bundle. No course-match, no professor-match: comparison and
    co-scheduling chunks legitimately talk about courses other than their own `course`
    field, and a stricter gate would break exactly the disambiguation queries we want.
    """
    call = call_model or claude
    valid = sorted(bundle_ids(bundle))
    base = _user_msg(bundle)
    msg = base
    answer = invented = None
    for n in range(1, max_attempts + 1):
        answer = call(SYSTEM, msg)
        cited, invented = audit_citations(answer, bundle)
        if verbose:
            print(f"    [audit] attempt {n}: cited={len(cited)} invented={len(invented)} {invented or ''}")
        if not invented:
            return answer
        msg = base + CORRECTION.format(n=n, bad=", ".join(invented),
                                       valid="\n".join(f"  - {v}" for v in valid))
    raise CitationAuditError(max_attempts, invented, answer)


# ── multi-course bundle: one retrieval pass per course, one synthesis call ──────
def get_multi_bundle(query, courses, k=4, recency=False):
    """Compare several courses in ONE answer. Each course keeps its own scoped evidence."""
    out = {"query": query, "courses": {}}
    for c in courses:
        b = get_bundle(query, course=c, k=k, recency=recency)
        out["courses"][c] = {"professors": b["professors"], "general": b["general"]}
    return out


# ── the model seam: Claude (key from env, never hardcoded) ─────────────────────
MODEL = "claude-sonnet-4-6"
_client = None

def claude(system, user, model=MODEL, effort="medium"):
    """Anthropic SDK. anthropic.Anthropic() resolves ANTHROPIC_API_KEY from the
    environment on its own — no key is ever read from or written to this file."""
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()          # env-resolved credentials
    msg = _client.messages.create(
        model=model,
        max_tokens=16000,                        # non-streaming: stay under SDK HTTP timeout
        thinking={"type": "adaptive"},           # budget_tokens is deprecated on 4.6
        output_config={"effort": effort},        # low | medium | high | max
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


# ── invariant check: every citation must trace to a chunk in the bundle ────────
def bundle_ids(bundle):
    ids = set()
    def walk(node):
        for pr in node.get("professors", {}).values():
            ids.update(c["id"] for c in pr["chunks"])
        ids.update(c["id"] for c in node.get("general", []))
    walk(bundle)
    for sub in bundle.get("courses", {}).values():
        walk(sub)
    return ids

def audit_citations(answer, bundle):
    """Return (cited_ids, invented_ids). Invented must always be empty."""
    import re
    known = bundle_ids(bundle)
    cited = set()
    for raw in re.findall(r"\[([^\]\n]+)\]", answer):
        head = raw.split("·")[0].strip().strip("`")
        if head:
            cited.add(head)
    return sorted(cited & known), sorted(c for c in cited - known if "#" in c)


if __name__ == "__main__":
    # No LLM call here — just show that provenance reaches the synthesis input.
    b = get_bundle("is 15-150 hard, who should I take it with", course="15-150")
    for prof, d in b["professors"].items():
        print(f"\n{prof} \u2014 {d['stats']}")
        for c in d["chunks"]:
            flag = "\u2713" if c["verified"] else "\u25cb"
            print(f"  {flag} [{c['id']}] {c['cite']} \u00b7 {c['date']} \u00b7 {c['url'] or 'link pending'}")
    if b["general"]:
        print("\nCourse-level (no professor):")
        for c in b["general"]:
            flag = "\u2713" if c["verified"] else "\u25cb"
            print(f"  {flag} [{c['id']}] {c['cite']} \u00b7 {c['date']} \u00b7 {c['url'] or 'link pending'}")
