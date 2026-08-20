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
