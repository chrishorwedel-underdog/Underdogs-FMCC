import { useState } from "react";
import { Minus, Plus, X } from "lucide-react";

export const POS_WEIGHTS = { GK: 2, DC: 4, DL: 2, DR: 2, DM: 2, MC: 3, AML: 2, AMR: 2, AMC: 2, ST: 3 };
export const STAFF_WEIGHTS = { "First-Team Coach": 3, "Youth Coach": 2, "Fitness Coach": 1, "Goalkeeping Coach": 1, Scout: 4, "Chief Scout": 1, Physio: 3, "Sports Scientist": 1,
  "Performance Analyst": 2, "Director of Football": 1, "General Manager": 1, "Assistant Manager": 1 };
export const PLAYER_AGE_PRESETS = { Balanced: { young: 2, prime: 2, experienced: 1, youth: 1, veteran: 1 }, Academy: { youth: 3, young: 2 }, "Prime age": { prime: 3, experienced: 1 }, Veterans: { experienced: 2, veteran: 3 } };
export const STAFF_AGE_PRESETS = { Balanced: { early: 1, established: 2, senior: 2, veteran: 1 }, "Up-and-coming": { early: 3, established: 1 }, Experienced: { senior: 2, veteran: 2, elder: 1 } };

export const split = (total, weights) => {
  const keys = Object.keys(weights).filter((k) => weights[k] > 0);
  const sum = keys.reduce((a, k) => a + weights[k], 0);
  if (!sum || !total) return {};
  const raw = keys.map((k) => [k, (total * weights[k]) / sum]);
  const out = Object.fromEntries(raw.map(([k, v]) => [k, Math.floor(v)]));
  let left = total - Object.values(out).reduce((a, b) => a + b, 0);
  raw.sort((a, b) => (b[1] % 1) - (a[1] % 1)).forEach(([k]) => { if (left > 0) { out[k] += 1; left -= 1; } });
  return Object.fromEntries(Object.entries(out).filter(([, v]) => v > 0));
};

export const Step = ({ n, title, hint, children, id }) => (
  <section className="card seed-step" data-testid={id}>
    <div className="seed-step-head"><span className="seed-num">{n}</span><div><b>{title}</b>{hint && <small className="note">{hint}</small>}</div></div>
    <div style={{ display: "grid", gap: 14 }}>{children}</div>
  </section>
);

export const Stepper = ({ label, v, set, picks, max, id }) => (
  <div className="seed-stepper" data-testid={id}>
    <div className="eyebrow">{label}</div>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <button className="btn seed-sq" onClick={() => set(Math.max(0, v - 1))} aria-label={`Fewer ${label}`} data-testid={`${id}-minus`}><Minus size={16} /></button>
      <input className="inp mono seed-big" type="number" min={0} max={max} value={v} onChange={(e) => set(Math.max(0, Math.min(max, Number(e.target.value) || 0)))} data-testid={`${id}-input`} />
      <button className="btn seed-sq" onClick={() => set(Math.min(max, v + 1))} aria-label={`More ${label}`} data-testid={`${id}-plus`}><Plus size={16} /></button>
    </div>
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{picks.map((p) => <button key={p} className={`btn seed-pick${v === p ? " btn-p" : ""}`} onClick={() => set(p)} data-testid={`${id}-pick-${p}`}>{p}</button>)}</div>
  </div>
);

export const Seg = ({ opts, v, set, id }) => (
  <div className="seg" style={{ justifySelf: "start", flexWrap: "wrap" }} data-testid={id}>
    {opts.map((o) => <button key={o} className={v === o ? "on" : ""} onClick={() => set(o)} data-testid={`${id}-${o.replace(/\s+/g, "-").toLowerCase()}`}>{o}</button>)}
  </div>
);

export const CountGrid = ({ keys, vals, set, id }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))", gap: "6px 14px" }}>
    {keys.map((k) => <label key={k} className="note" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 6 }}>{k}
      <input className="inp mono" style={{ width: 58, height: 30 }} type="number" min={0} max={100} value={vals[k] || 0} onChange={(e) => set({ ...vals, [k]: Math.max(0, Math.min(100, Number(e.target.value) || 0)) })} data-testid={`${id}-${k}`} /></label>)}
  </div>
);

export const Shares = ({ items, vals, set, id }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))", gap: "6px 14px" }}>
    {items.map(([k, label]) => <label key={k} className="note" style={{ display: "grid", gap: 2 }}><span>{label} <b style={{ color: "var(--text)" }}>{vals[k] || 0}</b></span>
      <input type="range" min={0} max={10} value={vals[k] || 0} onChange={(e) => set({ ...vals, [k]: Number(e.target.value) })} data-testid={`${id}-${k}`} /></label>)}
  </div>
);

export const Nations = ({ list, set, all, counts }) => {
  const [n, setN] = useState("");
  const tot = list.reduce((a, x) => a + x.share, 0) || 1;
  return (
    <div style={{ display: "grid", gap: 10 }} data-testid="seed-nations">
      {list.map((x, i) => <div key={x.nation} className="seed-nat" data-testid={`seed-nat-${x.nation}`}>
        <b style={{ minWidth: 120 }}>{x.nation}</b>
        <input type="range" min={1} max={10} value={x.share} style={{ flex: 1, minWidth: 100 }} onChange={(e) => set(list.map((y, j) => (j === i ? { ...y, share: Number(e.target.value) } : y)))} data-testid={`seed-nat-share-${x.nation}`} />
        <span className="mono note" style={{ width: 120, textAlign: "right" }} data-testid={`seed-nat-count-${x.nation}`}>{Math.round((x.share / tot) * 100)}% · {counts[x.nation] || 0} people</span>
        <button className="ib" disabled={list.length === 1} onClick={() => set(list.filter((_, j) => j !== i))} aria-label={`Remove ${x.nation}`} data-testid={`seed-nat-remove-${x.nation}`}><X size={13} /></button>
      </div>)}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <select className="inp" style={{ width: 220, height: 34 }} value={n} onChange={(e) => setN(e.target.value)} data-testid="seed-nat-select">
          <option value="">Add a nationality…</option>{all.filter((x) => !list.some((y) => y.nation === x)).map((x) => <option key={x}>{x}</option>)}</select>
        <button className="btn" disabled={!n} onClick={() => { set([...list, { nation: n, share: 5 }]); setN(""); }} data-testid="seed-nat-add"><Plus size={13} />Add</button>
        <button className="btn" onClick={() => set(list.map((x) => ({ ...x, share: 5 })))} data-testid="seed-nat-even">Make them equal</button>
      </div>
    </div>
  );
};
