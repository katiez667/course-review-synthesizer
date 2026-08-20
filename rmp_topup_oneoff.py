"""One-off: RMP top-up for near-miss courses (2+ chunks, single source). Only touches
professors already named in the existing corpus text -- no invented names, no invented
courses. Appends to rmp_corpus.json in the exact schema the existing entries use.

Handles two RMP data quirks the original 20 entries never happened to hit:
  - wouldTakeAgainPercent == -1 is RMP's "not enough responses to compute this" sentinel,
    not a literal -1%. Rendered as prose instead of a fabricated percentage.
  - percentages come back as unrounded floats (e.g. 85.7143) -- rounded to match the
    whole-number style every existing entry uses.
"""
import base64, json, re, sys
import rmp_client as rmp

TOPUP = {
    "07-128": ["Jacobo Carrasquel", "Tom Cortina"],
    "15-259": ["Mor Harchol-Balter"],
    "15-312": ["Bob Harper", "Jan Hoffmann"],
    "15-330": ["Bryan Parno"],
    "15-411": ["Seth Goldstein"],
    "15-445": ["Andy Pavlo", "Jignesh Patel"],
    "15-462": ["Keenan Crane"],
    "15-604": ["David Eckhardt"],
    "15-712": ["Phil Gibbons"],
    "15-721": ["Andy Pavlo"],
    "15-859": ["David Woodruff", "Pravesh Kothari"],
}
# 07-131, 10-301, 15-122, 15-210, 15-400, 15-745, 76-106, 76-107 have no named
# professor anywhere in the existing corpus -> nothing honest to look up, skipped.

def slug(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

def rmp_url(node):
    raw = base64.b64decode(node["id"] + "===").decode()  # "Teacher-2450311"
    num = raw.split("-", 1)[1]
    return f"https://www.ratemyprofessors.com/professor/{num}"

def make_text(name, node):
    if not node.get("numRatings"):
        return f"{name} has no RateMyProfessors ratings yet (0 reviews on file)."
    wta = node["wouldTakeAgainPercent"]
    wta_str = "not enough responses to show a would-take-again rate" if wta == -1 else f"{round(wta)}% would take again"
    return (f"{name} overall {node['avgRating']}/5, {wta_str}, "
            f"difficulty {node['avgDifficulty']}/5, based on {node['numRatings']} ratings.")

def main():
    all_names = sorted({n for names in TOPUP.values() for n in names})
    print(f"looking up {len(all_names)} professors (cached ones cost no network call)...")
    results = rmp.lookup_many(all_names)
    for name, node in results.items():
        print(f"  {name:<22} {'no RMP match' if node is None else 'id=' + node['id']}")

    existing = json.load(open("rmp_corpus.json"))
    print(f"\nrmp_corpus.json currently has {len(existing)} entries")
    existing_ids = {e["id"] for e in existing}
    added, skipped_dupe, skipped_nomatch = [], [], []

    for course, names in TOPUP.items():
        for name in names:
            node = results.get(name)
            if node is None:
                skipped_nomatch.append((course, name)); continue
            eid = f"rmp-{slug(name)}-{course}"
            if eid in existing_ids:
                skipped_dupe.append(eid); continue
            entry = {"id": eid, "source": "rmp", "course": course, "thread": f"RMP {name}",
                      "professor": name, "date": "2026-08", "url": rmp_url(node),
                      "text": make_text(name, node)}
            existing.append(entry); existing_ids.add(eid); added.append(entry)

    json.dump(existing, open("rmp_corpus.json", "w"), indent=2, ensure_ascii=False)
    print(f"\nadded {len(added)} new rmp chunks -> file now has {len(existing)} entries:")
    for e in added:
        print(f"  {e['id']:<32} {e['text']}")
    if skipped_nomatch:
        print(f"\nskipped (no RMP match found, nothing invented):")
        for course, name in skipped_nomatch:
            print(f"  {course} / {name}")
    if skipped_dupe:
        print(f"\nskipped (already present): {skipped_dupe}")

if __name__ == "__main__":
    main()
