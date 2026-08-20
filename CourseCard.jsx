/**
 * CourseCard.jsx — renders ONE frozen card from demo_data/.
 *
 * Everything here is display-only. No API calls, no mock data, no re-derivation:
 * the answers, the professor verdicts, the source mix and the receipts were all
 * decided at freeze time by freeze_cards.py and are read verbatim from JSON.
 *
 * The two corpus invariants are load-bearing in the UI:
 *   1. A receipt with verified=false renders "link pending" and is never linked.
 *      No URL is ever constructed here.
 *   2. Professors are never averaged. professor_split.professors is rendered as
 *      separate panels, each with its own stats — green for seek_out, rust for avoid.
 *
 * Usage:
 *   <CourseCard card={parsedJson} />                  // you already loaded it
 *   <CourseCard cardId="15-150" />                    // fetches demo_data/15-150.json
 */

import React, { useState, useEffect, useMemo, useRef } from "react";
import "./CourseCard.css";

/* ─────────────────────────── citations ───────────────────────────
 * Synthesis emits [id · cite · date · url] or [id · cite · date · link pending].
 * The id is the pid and the only part we trust — everything else we re-read from
 * the receipt, so a citation can never display a link the receipt doesn't have.
 * (No markdown links exist in the frozen prose, so a bare \[...\] is unambiguous.)
 */
const CITE_RE = /\[([^\]\n]+)\]/g;

function splitCitations(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(CITE_RE)) {
    const raw = m[1];
    if (!raw.includes("·")) continue; // not a citation, leave as literal text
    if (m.index > last) out.push({ t: "text", v: text.slice(last, m.index) });
    out.push({ t: "cite", id: raw.split("·")[0].trim().replace(/`/g, "") });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ t: "text", v: text.slice(last) });
  return out;
}

const SOURCE_LABEL = { reddit: "r/cmu", rmp: "RMP", blog: "blog" };

function Cite({ id, receipts, onJump }) {
  const r = receipts[id];
  if (!r) {
    // Post-gate this should be impossible. Show it loudly rather than swallow it.
    return <sup className="cite cite-missing" title={`unresolved citation: ${id}`}>?</sup>;
  }
  const label = SOURCE_LABEL[r.source] || r.source || "src";
  return (
    <sup
      className={`cite cite-${r.source} ${r.verified ? "is-verified" : "is-pending"}`}
      title={`${r.id}\n${r.cite}\n${r.date || "undated"}\n${r.url || "link pending"}`}
      onClick={() => onJump(id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onJump(id)}
    >
      {label}
      <span className="cite-flag">{r.verified ? "✓" : "○"}</span>
    </sup>
  );
}

/* ─────────────────────── inline + block markdown ───────────────────────
 * A deliberately small renderer for exactly what the frozen prose contains:
 * h2-h4, hr, ul/ol, blockquote, pipe tables, **bold**, *italic*, and citations.
 * No markdown links and no code fences appear in demo_data/, so neither is handled.
 */
function Inline({ text, receipts, onJump }) {
  const nodes = [];
  splitCitations(text).forEach((piece, i) => {
    if (piece.t === "cite") {
      nodes.push(<Cite key={i} id={piece.id} receipts={receipts} onJump={onJump} />);
      return;
    }
    // bold before italic so **x** doesn't get eaten by the single-star rule
    const parts = piece.v.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/g);
    parts.forEach((p, j) => {
      const key = `${i}-${j}`;
      if (/^\*\*[^*]+\*\*$/.test(p)) nodes.push(<strong key={key}>{p.slice(2, -2)}</strong>);
      else if (/^\*[^*\n]+\*$/.test(p)) nodes.push(<em key={key}>{p.slice(1, -1)}</em>);
      else if (p) nodes.push(<React.Fragment key={key}>{p}</React.Fragment>);
    });
  });
  return <>{nodes}</>;
}

function isTableRow(l) {
  return /^\s*\|.*\|\s*$/.test(l);
}
function isTableDivider(l) {
  return /^\s*\|[\s:|-]+\|\s*$/.test(l);
}
function cells(l) {
  return l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
}

function Markdown({ md, receipts, onJump }) {
  const blocks = useMemo(() => {
    const lines = (md || "").split("\n");
    const out = [];
    let i = 0;
    const inline = (t) => t;

    while (i < lines.length) {
      const l = lines[i];

      if (!l.trim()) { i++; continue; }

      if (/^(---|\*\*\*|___)\s*$/.test(l)) { out.push({ k: "hr" }); i++; continue; }

      const h = l.match(/^(#{2,4})\s+(.*)$/);
      if (h) { out.push({ k: "h", level: h[1].length, v: inline(h[2]) }); i++; continue; }

      if (isTableRow(l) && isTableRow(lines[i + 1] || "") && isTableDivider(lines[i + 1])) {
        const head = cells(l);
        i += 2;
        const rows = [];
        while (i < lines.length && isTableRow(lines[i])) { rows.push(cells(lines[i])); i++; }
        out.push({ k: "table", head, rows });
        continue;
      }

      if (/^>\s?/.test(l)) {
        const buf = [];
        while (i < lines.length && /^>\s?/.test(lines[i])) { buf.push(lines[i].replace(/^>\s?/, "")); i++; }
        out.push({ k: "quote", v: buf.join(" ") });
        continue;
      }

      if (/^\s*[-*]\s+/.test(l) || /^\s*\d+\.\s+/.test(l)) {
        const ordered = /^\s*\d+\.\s+/.test(l);
        const items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) {
          items.push(lines[i].replace(/^\s*([-*]|\d+\.)\s+/, ""));
          i++;
        }
        out.push({ k: "list", ordered, items });
        continue;
      }

      const buf = [];
      while (
        i < lines.length && lines[i].trim() &&
        !/^(#{2,4})\s/.test(lines[i]) && !/^(---|\*\*\*|___)\s*$/.test(lines[i]) &&
        !/^\s*([-*]|\d+\.)\s+/.test(lines[i]) && !/^>\s?/.test(lines[i]) && !isTableRow(lines[i])
      ) { buf.push(lines[i]); i++; }
      out.push({ k: "p", v: buf.join(" ") });
    }
    return out;
  }, [md]);

  const I = (t) => <Inline text={t} receipts={receipts} onJump={onJump} />;

  return (
    <div className="md">
      {blocks.map((b, n) => {
        switch (b.k) {
          case "hr":
            return <hr key={n} />;
          case "h": {
            const Tag = `h${b.level}`;
            return <Tag key={n}>{I(b.v)}</Tag>;
          }
          case "quote":
            return <blockquote key={n}>{I(b.v)}</blockquote>;
          case "list": {
            const Tag = b.ordered ? "ol" : "ul";
            return <Tag key={n}>{b.items.map((it, m) => <li key={m}>{I(it)}</li>)}</Tag>;
          }
          case "table":
            return (
              <div className="table-scroll" key={n}>
                <table>
                  <thead><tr>{b.head.map((c, m) => <th key={m}>{I(c)}</th>)}</tr></thead>
                  <tbody>
                    {b.rows.map((r, m) => (
                      <tr key={m}>{r.map((c, o) => <td key={o}>{I(c)}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          default:
            return <p key={n}>{I(b.v)}</p>;
        }
      })}
    </div>
  );
}

/* ─────────────────────────── professor split ─────────────────────────── */

const VERDICT = {
  seek_out: { cls: "seek", label: "Seek out" },
  avoid:    { cls: "avoid", label: "Avoid" },
  unknown:  { cls: "neutral", label: "Not enough signal" },
};

function Stat({ label, value, suffix = "" }) {
  return (
    <div className="stat">
      <div className="stat-v">{value === null || value === undefined ? "—" : `${value}${suffix}`}</div>
      <div className="stat-l">{label}</div>
    </div>
  );
}

function ProfessorSplit({ split, receipts, onJump }) {
  if (!split || !split.available) {
    return (
      <section className="split split-empty">
        <h3 className="section-h">Professors</h3>
        <div className="panel neutral">
          <p className="empty-note">
            {split?.reason || "No per-instructor ratings for this course in the corpus."}
          </p>
          <p className="empty-sub">
            Per-professor panels appear only where the corpus carries structured
            instructor stats. Nothing is averaged or inferred to fill this space.
          </p>
        </div>
      </section>
    );
  }
  return (
    <section className="split">
      <h3 className="section-h">Professors &mdash; reported separately, never averaged</h3>
      <div className="panels">
        {split.professors.map((p) => {
          const v = VERDICT[p.verdict] || VERDICT.unknown;
          return (
            <div className={`panel ${v.cls}`} key={p.name}>
              <div className="panel-top">
                <span className="verdict">{v.label}</span>
                <h4>{p.name}</h4>
              </div>
              <div className="stats">
                <Stat label="quality" value={p.stats?.quality} suffix="/5" />
                <Stat label="would take again" value={p.stats?.would_take_again_pct} suffix="%" />
                <Stat label="difficulty" value={p.stats?.difficulty} suffix="/5" />
              </div>
              <div className="panel-receipts">
                {p.receipt_ids.map((id) => {
                  const r = receipts[id];
                  if (!r) return null;
                  return (
                    <button className="mini-receipt" key={id} onClick={() => onJump(id)}>
                      <span className={`dot dot-${r.source}`} />
                      <span className="mini-text">{r.text}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* ─────────────────────────── source mix ─────────────────────────── */

function SourceMix({ mix }) {
  if (!mix || !mix.total) return null;
  const seg = [
    { k: "reddit", n: mix.reddit }, { k: "rmp", n: mix.rmp }, { k: "blog", n: mix.blog },
  ].filter((s) => s.n > 0);
  return (
    <div className="mix">
      <div className="mix-bar">
        {seg.map((s) => (
          <span key={s.k} className={`seg seg-${s.k}`} style={{ flexGrow: s.n }}
                title={`${s.n} ${s.k}`} />
        ))}
      </div>
      <div className="mix-legend">
        {seg.map((s) => (
          <span key={s.k} className="mix-item">
            <span className={`dot dot-${s.k}`} />{SOURCE_LABEL[s.k]} {s.n}
          </span>
        ))}
        <span className="mix-item mix-verified">
          {mix.verified}/{mix.total} linked
          {mix.unverified > 0 && <em> &middot; {mix.unverified} link pending</em>}
        </span>
      </div>
    </div>
  );
}

/* ─────────────────────────── receipts ─────────────────────────── */

function Receipt({ r, highlighted, refFn }) {
  return (
    <li ref={refFn} className={`receipt ${highlighted ? "hl" : ""}`}>
      <div className="r-head">
        <span className={`badge badge-${r.source}`}>{SOURCE_LABEL[r.source] || r.source}</span>
        {r.verified ? (
          <a className="badge badge-verified" href={r.url} target="_blank" rel="noreferrer">
            &#10003; verified source
          </a>
        ) : (
          <span className="badge badge-pending" title="Hand-pasted: no verified link exists for this chunk.">
            &#9675; link pending
          </span>
        )}
        <span className="r-date">{r.date || "undated"}</span>
        {r.course && <span className="r-course">{r.course}</span>}
        {r.professor && <span className="r-prof">{r.professor}</span>}
      </div>
      <p className="r-text">{r.text}</p>
      <div className="r-foot">
        <code className="r-id">{r.id}</code>
        <span className="r-cite">{r.cite}</span>
      </div>
    </li>
  );
}

function Receipts({ receipts, ids, open, setOpen, highlighted, itemRefs }) {
  const list = ids.map((id) => receipts[id]).filter(Boolean);
  return (
    <section className="receipts">
      <button className="receipts-toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className={`chev ${open ? "down" : ""}`}>&#9656;</span>
        Receipts <span className="count">{list.length}</span>
        <span className="receipts-sub">every claim above traces to one of these</span>
      </button>
      {open && (
        <ul className="receipt-list">
          {list.map((r) => (
            <Receipt key={r.id} r={r} highlighted={highlighted === r.id}
                     refFn={(el) => (itemRefs.current[r.id] = el)} />
          ))}
        </ul>
      )}
    </section>
  );
}

/* ─────────────────────────── the card ─────────────────────────── */

export default function CourseCard({ card: cardProp, cardId, basePath = "demo_data" }) {
  const [card, setCard] = useState(cardProp || null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(0);
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(null);
  const itemRefs = useRef({});

  useEffect(() => {
    if (cardProp) { setCard(cardProp); return; }
    if (!cardId) return;
    let alive = true;
    fetch(`${basePath}/${cardId}.json`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status} loading ${cardId}.json`); return r.json(); })
      .then((j) => alive && setCard(j))
      .catch((e) => alive && setErr(e.message));
    return () => { alive = false; };
  }, [cardProp, cardId, basePath]);

  if (err) return <div className="card card-err">Could not load card: {err}</div>;
  if (!card) return <div className="card card-loading">Loading&hellip;</div>;

  const receipts = card.receipts || {};
  const tabs = [
    { key: "overview", label: "Overview", ...card.headline },
    ...(card.facets || []),
  ];
  const active = tabs[Math.min(tab, tabs.length - 1)];

  // Receipts shown = the ones this tab actually cites, so the drawer tracks the tab.
  const tabIds = (active.cited_ids || []).filter((id) => receipts[id]);
  const allIds = Object.keys(receipts).sort();

  const jump = (id) => {
    setOpen(true);
    setHighlighted(id);
    requestAnimationFrame(() => {
      const el = itemRefs.current[id];
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  };

  const isMulti = card.kind === "multi";
  const heading = isMulti ? (card.courses || []).join(" · ") : card.course;

  return (
    <article className="card">
      <header className="card-head">
        <div className="ch-left">
          <div className="course-no">{heading}</div>
          {card.title && <h2 className="course-title">{card.title}</h2>}
        </div>
        <div className="ch-right">
          <SourceMix mix={card.source_mix} />
          <div className="frozen">
            frozen {(card.frozen_at || "").slice(0, 10)} &middot; {card.model}
            {card.retrieval?.recency && <> &middot; recency-weighted</>}
          </div>
        </div>
      </header>

      <div className="question">
        <span className="q-mark">Q</span>
        <p>{active.question}</p>
      </div>

      <nav className="tabs" role="tablist">
        {tabs.map((t, i) => (
          <button key={t.key} role="tab" aria-selected={i === tab}
                  className={`tab ${i === tab ? "on" : ""}`}
                  onClick={() => { setTab(i); setHighlighted(null); }}>
            {t.label}
          </button>
        ))}
      </nav>

      <div className="answer">
        <Markdown md={active.answer_md} receipts={receipts} onJump={jump} />
      </div>

      {isMulti ? (
        <section className="split">
          <h3 className="section-h">Per-course evidence</h3>
          <div className="panels multi">
            {Object.entries(card.per_course || {}).map(([c, d]) => (
              <div className="panel neutral compact" key={c}>
                <div className="panel-top">
                  <span className="verdict">{c}</span>
                  <h4>{d.title}</h4>
                </div>
                <SourceMix mix={d.source_mix} />
                {!d.professor_split?.available && (
                  <p className="empty-sub">{d.professor_split?.reason}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      ) : (
        <ProfessorSplit split={card.professor_split} receipts={receipts} onJump={jump} />
      )}

      <Receipts receipts={receipts} ids={tabIds.length ? tabIds : allIds}
                open={open} setOpen={setOpen}
                highlighted={highlighted} itemRefs={itemRefs} />
    </article>
  );
}
