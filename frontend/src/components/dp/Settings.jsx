import { useEffect, useState } from "react";
import { RotateCcw, History } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { RuleItem, ImpactSave } from "@/components/rules/RuleItem";

const SECTIONS = {
  score: ["Performance Score", "Weights of match rating and role output, role groups A/B/C, comparison group size, youth weighting and the expected-level band used to pick comparison players."],
  metrics: ["Role metrics per position", "Statistics in each role group, comma separated. Each becomes a percentile first; several in one group are averaged."],
  standins: ["Stand-in statistics", "Used when a statistic is missing, for the player and the comparison group alike."],
  reverse: ["Lower is better", "Bad-outcome statistics scored in reverse, comma separated."],
  bands: ["Score bands", "From a score of at least (left) to the base change (right), highest first, ending at 0."],
  tiers: ["Growth tiers", "Award ranges and the minutes or percentiles each tier needs."],
  decline: ["Decline", "Every requirement must be met for an ordinary or severe decline."],
  age: ["Age deduction", "Age at season start (left) and the points taken off growth (right)."],
  growth_taper: ["Growth taper", "Players nearer the top of the potential scale keep a smaller share of earned growth. Left: the potential level; right: the share kept in %."],
  decline_taper: ["Decline taper", "Players higher up the potential scale take a larger share of earned loss. Left: the potential level; right: the share taken in %."],
  winter: ["Winter review", "Minutes needed, share of the provisional growth awarded, its maximum and the youth ceiling."],
  limits: ["Limits", "Loss floor, the highest potential allowed, seasonal maximums and what's needed to take winter points back."],
  batch_size: ["Batch size", "Players reviewed per run; the rest carry over to the next run."],
};
const words = (k) => k.replace(/_/g, " ").replace(/90$/, " / 90").replace(/^./, (c) => c.toUpperCase());

const Num = ({ v, set, id }) => <input className="inp mono" type="number" style={{ width: 90, height: 30 }} value={v} onChange={(e) => set(Number(e.target.value))} data-testid={id} />;

const Field = ({ v, set, id, labels }) => {
  if (typeof v === "number") return <Num v={v} set={set} id={id} />;
  if (Array.isArray(v) && Array.isArray(v[0])) {
    return (
      <div style={{ display: "grid", gap: 4 }}>
        {v.map((row, i) => <div key={i} style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {row.map((x, j) => <Num key={j} v={x} set={(n) => set(v.map((r, k) => (k === i ? r.map((y, m) => (m === j ? n : y)) : r)))} id={`${id}-${i}-${j}`} />)}
          <button className="ib" onClick={() => set(v.filter((_, k) => k !== i))} aria-label="Remove row" data-testid={`${id}-del-${i}`}>×</button></div>)}
        <button className="btn" style={{ width: "fit-content", height: 26, fontSize: 12 }} onClick={() => set([...v, [...v[v.length - 1]]])} data-testid={`${id}-add`}>Add row</button>
      </div>);
  }
  if (Array.isArray(v)) return <div><input className="inp" style={{ width: 320, height: 30 }} value={v.join(", ")} onChange={(e) => set(e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} data-testid={id} />
    <small style={{ display: "block", color: "var(--dim)" }}>{v.map((x) => labels?.metrics?.[x] || x).join(" · ")}</small></div>;
  if (typeof v === "string") return <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}><input className="inp" style={{ width: 200, height: 30 }} value={v} onChange={(e) => set(e.target.value.trim())} data-testid={id} /><small>{labels?.metrics?.[v]}</small></span>;
  return (
    <div style={{ display: "grid", gap: 6, paddingLeft: 10, borderLeft: "1px solid var(--line)" }}>
      {Object.entries(v).map(([k, x]) => <div key={k} style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <small style={{ width: 190 }}>{labels?.positions?.[k] || labels?.metrics?.[k] || words(k)}</small>
        <Field v={x} set={(n) => set({ ...v, [k]: n })} id={`${id}-${k}`} labels={labels} /></div>)}
    </div>);
};

const fmt = (v, def) => (typeof v === "number" || typeof v === "string" ? String(v) : JSON.stringify(v) === JSON.stringify(def) ? "Rulesheet values" : "Your own values");

export const DPSettings = () => {
  const { data } = useGet("dp-settings", "/dp/settings");
  const act = useAct();
  const [d, setD] = useState(null);
  const [note, setNote] = useState("");
  useEffect(() => { if (data) { setD(structuredClone(data.data)); } }, [data]);
  if (!data || !d) return <p className="note">Loading settings…</p>;
  const edited = Object.keys(SECTIONS).filter((k) => JSON.stringify(d[k]) !== JSON.stringify(data.data[k]));
  const keys = ["dp-settings", "dp-overview"];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 280px", gap: 16 }} className="fit-grid" data-testid="dp-settings">
      <div style={{ display: "grid", gap: 12 }}>
        {Object.entries(SECTIONS).map(([k, [title, help]]) => {
          const differs = JSON.stringify(d[k]) !== JSON.stringify(data.defaults[k]);
          return (
          <div key={k} data-testid={`dp-set-${k}`}>
            <RuleItem id={`dp-${k}`} title={title} help={help} now={fmt(d[k], data.defaults[k])} def={fmt(data.defaults[k], data.defaults[k])} changedAt={data.changed_at?.[k]}
              differs={differs} onReset={() => setD({ ...d, [k]: structuredClone(data.defaults[k]) })}>
              {differs && <span className="st a" style={{ display: "none" }} data-testid={`dp-set-changed-${k}`}>Differs from the rulesheet</span>}
              <Field v={d[k]} set={(n) => setD({ ...d, [k]: n })} id={`dp-f-${k}`} labels={data.labels} />
            </RuleItem>
          </div>);
        })}
      </div>
      <div style={{ display: "grid", gap: 12, alignContent: "start", position: "sticky", top: 70 }}>
        <div data-testid="dp-set-save-card">
        <ImpactSave dirty={edited.length > 0} draftKey={JSON.stringify(d)} check={() => api.post("/dp/settings/impact", { data: d })}
          save={() => act(() => api.put("/dp/settings", { data: d, note: note || "Edited settings" }), "Settings saved", keys).then((r) => { if (r) { setNote(""); } return r; })}
          summary={`You've changed: ${edited.map((k) => SECTIONS[k][0]).join(", ")}. Past reviews keep the settings they used; the next review uses these.`}>
          <input className="inp" style={{ marginTop: 10 }} placeholder="What changed (optional)" value={note} maxLength={120} onChange={(e) => setNote(e.target.value)} data-testid="dp-set-note" />
          <button className="btn" style={{ marginTop: 8 }} onClick={() => window.confirm("Reset every Dynamic Potential setting to the rulesheet?") && act(() => api.post("/dp/settings/reset"), "Everything reset to the rulesheet", keys)} data-testid="dp-set-reset-all"><RotateCcw size={13} />Reset everything</button>
          <small style={{ display: "block", marginTop: 6, color: "var(--dim)" }}>One set for all careers · version {data.version}</small>
        </ImpactSave></div>
        <div className="card" data-testid="dp-set-history"><div className="ttl"><History size={13} />History</div>
          {data.history.map((h) => <div key={h.version} className="row"><div style={{ flex: 1 }}>v{h.version}<small>{h.note} · {h.at?.slice(0, 16).replace("T", " ")}</small></div>
            <button className="btn" style={{ height: 26, fontSize: 12 }} onClick={() => act(() => api.post(`/dp/settings/restore/${h.version}`), `Version ${h.version} restored`, keys)} data-testid={`dp-set-restore-${h.version}`}>Restore</button></div>)}
          {!data.history.length && <p className="note">Using the rulesheet as written.</p>}
        </div>
      </div>
    </div>
  );
};
