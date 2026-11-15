import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { usePersist } from "@/lib/remember";

const MIN = 50;

// Column widths the user can drag (or nudge with arrow keys); remembered per career.
export const useColWidths = (key, defaults) => {
  const [saved, setSaved] = usePersist(`colw:${key}`, {});
  const [live, setLive] = useState(null);
  const drag = useRef(null);
  const widths = { ...defaults, ...saved, ...(live || {}) };
  const start = (col, e) => {
    e.preventDefault();
    drag.current = { col, x: e.clientX, w: widths[col] };
    const move = (ev) => { const d = drag.current; setLive({ [d.col]: Math.max(MIN, Math.round(d.w + ev.clientX - d.x)) }); };
    const up = (ev) => {
      const d = drag.current;
      setSaved((s) => ({ ...s, [d.col]: Math.max(MIN, Math.round(d.w + ev.clientX - d.x)) }));
      setLive(null);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  const nudge = (col, by) => setSaved((s) => ({ ...s, [col]: Math.max(MIN, (s[col] ?? defaults[col]) + by) }));
  const reset = () => setSaved({});
  const total = Object.keys(defaults).reduce((a, k) => a + widths[k], 0);
  return { widths, start, nudge, reset, total, changed: Object.keys(saved).length > 0 };
};

export const ColGroup = ({ cols, c }) => <colgroup>{cols.map((k) => <col key={k} style={{ width: c.widths[k] }} />)}</colgroup>;

export const ResizeTh = ({ col, c, label, className = "", title, id, sort }) => (
  <th className={`rz-th ${className}${sort ? " sortable" : ""}`} title={title} onClick={sort?.onClick} aria-sort={sort?.dir ? (sort.dir === "asc" ? "ascending" : "descending") : undefined} data-testid={`${id}-head-${col}`}>
    {label}{sort?.dir && <span className="sort-ar">{sort.dir === "asc" ? " \u25B2" : " \u25BC"}</span>}
    <span className="rz-h" role="separator" aria-orientation="vertical" aria-label={`Resize ${label || "column"}`} tabIndex={0}
      onPointerDown={(e) => { e.stopPropagation(); c.start(col, e); }} onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); c.nudge(col, e.key === "ArrowLeft" ? -10 : 10); } }}
      data-testid={`${id}-resize-${col}`} />
  </th>
);

const heads = (t) => [...(t?.tHead?.rows[0]?.cells || [])];

// Each body cell carries its heading, so on phones a row can be shown as a labelled card.
export const labelCells = (t) => {
  const ls = heads(t).map((th) => th.textContent.replace(/[\u2191\u2193\u25b2\u25bc]/g, "").trim());
  [...(t?.tBodies?.[0]?.rows || [])].forEach((tr) => [...tr.cells].forEach((td, i) => { if (td.getAttribute("data-label") !== (ls[i] || "")) td.setAttribute("data-label", ls[i] || ""); }));
};

export const useCardLabels = () => {
  const [el, setEl] = useState(null);
  useLayoutEffect(() => { if (el) { el.classList.add("tbl-std"); labelCells(el); } });
  return setEl;
};

// Show long lists 50 rows at a time.
export const usePaged = (rows, size = 50) => {
  const [n, setN] = useState(size);
  const list = rows || [];
  const more = list.length > n ? { left: list.length - n, next: Math.min(size, list.length - n), show: () => setN(n + size) } : null;
  return [list.slice(0, n), more];
};

export const ShowMore = ({ more, id }) => (more ? <button className="btn show-more" onClick={more.show} data-testid={`${id}-show-more`}>Show {more.next} more ({more.left} left)</button> : null);
const names = (ths) => ths.map((th, i) => `${i}:${th.textContent.replace(/[↑↓▲▼]/g, "").trim()}`);

// Drop-in resizable columns for any existing <table>: attach `ref`, widths remembered per career by heading.
export const useResizableTable = (key) => {
  const [el, setEl] = useState(null);
  const [saved, setSaved] = usePersist(`colw:${key}`, {});
  const savedRef = useRef(saved);
  savedRef.current = saved;
  const [hidden, setHidden] = usePersist(`colhide:${key}`, []);
  const [labels, setLabels] = useState([]);

  useLayoutEffect(() => {
    const t = el;
    if (!t) return;
    const ths = heads(t);
    const ns = names(ths);
    const labs = ns.map((n) => n.split(":").slice(1).join(":"));
    if (labs.join("|") !== labels.join("|")) setLabels(labs); // eslint-disable-line react-hooks/exhaustive-deps
    const off = labs.map((l) => !!l && hidden.includes(l));
    const on = ns.length > 0 && ns.every((n) => saved[n]);
    ths.forEach((th, i) => {
      th.classList.add("rz-th");
      let h = th.querySelector(":scope > .rz-h");
      if (!h) {
        h = document.createElement("span");
        h.className = "rz-h";
        h.tabIndex = 0;
        h.setAttribute("role", "separator");
        h.setAttribute("aria-label", `Resize ${th.textContent.trim() || "column"}`);
        th.appendChild(h);
      }
      h.setAttribute("data-testid", `${key}-resize-${i}`);
      h.dataset.i = String(i);
      th.style.width = on ? `${saved[ns[i]]}px` : "";
      th.style.display = off[i] ? "none" : "";
    });
    [...(t.tBodies?.[0]?.rows || [])].forEach((tr) => [...tr.cells].forEach((td, i) => { const d = off[i] ? "none" : ""; if (td.style.display !== d) td.style.display = d; }));
    t.classList.toggle("rz-on", on);
    t.classList.add("tbl-std");
    labelCells(t);
    t.style.width = on ? `${ns.reduce((a, n, i) => a + (off[i] ? 0 : saved[n]), 0)}px` : "";
  });

  useEffect(() => {
    const t = el;
    if (!t) return undefined;
    const commit = (ths, ws) => { const ns = names(ths); setSaved({ ...savedRef.current, ...Object.fromEntries(ns.map((n, i) => [n, ws[i]])) }); };
    const down = (e) => {
      const h = e.target.closest?.(".rz-h");
      if (!h || !t.contains(h)) return;
      e.preventDefault();
      e.stopPropagation();
      const ths = heads(t);
      const ws = ths.map((th) => Math.round(th.getBoundingClientRect().width));
      const i = Number(h.dataset.i), x0 = e.clientX, w0 = ws[i];
      t.classList.add("rz-on");
      ths.forEach((th, j) => { th.style.width = `${ws[j]}px`; });
      const move = (ev) => {
        ws[i] = Math.max(MIN, Math.round(w0 + ev.clientX - x0));
        ths[i].style.width = `${ws[i]}px`;
        t.style.width = `${ws.reduce((a, b) => a + b, 0)}px`;
      };
      const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); commit(ths, ws); };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
    };
    const click = (e) => { if (e.target.closest?.(".rz-h")) { e.stopPropagation(); e.preventDefault(); } };
    const key = (e) => {
      const h = e.target.closest?.(".rz-h");
      if (!h || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) return;
      e.preventDefault();
      e.stopPropagation();
      const ths = heads(t);
      const ws = ths.map((th) => Math.round(th.getBoundingClientRect().width));
      const i = Number(h.dataset.i);
      ws[i] = Math.max(MIN, ws[i] + (e.key === "ArrowLeft" ? -10 : 10));
      commit(ths, ws);
    };
    t.addEventListener("pointerdown", down, true);
    t.addEventListener("click", click, true);
    t.addEventListener("keydown", key, true);
    return () => { t.removeEventListener("pointerdown", down, true); t.removeEventListener("click", click, true); t.removeEventListener("keydown", key, true); };
  }, [el]); // eslint-disable-line react-hooks/exhaustive-deps

  return { ref: setEl, reset: () => setSaved({}), changed: Object.keys(saved).length > 0,
    labels: labels.filter(Boolean), hidden, toggle: (l) => setHidden((h) => (h.includes(l) ? h.filter((x) => x !== l) : [...h, l])), showAll: () => setHidden([]) };
};

const ColumnPicker = ({ rz, id }) => {
  const [open, setOpen] = useState(false);
  if (!rz.labels?.length) return null;
  return <>
    <button className="btn" onClick={() => setOpen(!open)} aria-expanded={open} data-testid={`${id}-columns`}>Columns{rz.hidden.length ? ` (${rz.hidden.length} hidden)` : ""}</button>
    {open && <div className="card col-pick" data-testid={`${id}-columns-menu`}>
      {rz.labels.map((l, i) => <label key={l}><input type="checkbox" checked={!rz.hidden.includes(l)} disabled={i === 0} onChange={() => rz.toggle(l)} data-testid={`${id}-col-${i}`} />{l}</label>)}
      {rz.hidden.length > 0 && <button className="btn" onClick={rz.showAll} data-testid={`${id}-columns-all`}>Show all columns</button>}</div>}
  </>;
};

export const ResetWidths = ({ rz, id }) => (
  <div className="tbl-tools no-print"><ColumnPicker rz={rz} id={id} />{rz.changed && <button className="btn" onClick={rz.reset} data-testid={`${id}-reset-widths`}>Reset column widths</button>}</div>
);
