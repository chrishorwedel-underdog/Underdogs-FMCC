import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from "recharts";
import { GitCompare, X } from "lucide-react";
import { useGet } from "@/lib/ui";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { money, openDossier } from "./StatsTable";

const band = (v) => (v >= 16 ? "#34D399" : v >= 13 ? "#A3E635" : v >= 10 ? "#F2B54A" : "#FF6E6E");
const COLORS = ["#4C8DFF", "#34D399", "#F2B54A", "#FF6E6E", "#A78BFA"];
const RADAR = ["npxg", "xa", "kp", "progp", "drb", "tkw", "intc", "prr", "aerw", "pcmp"];
const NAMES = { npxg: "npxG", xa: "xA", kp: "Key passes", progp: "Prog. passes", drb: "Dribbles", tkw: "Tackles won", intc: "Interceptions", prr: "Pressure success", aerw: "Aerials won", pcmp: "Passes completed" };

const Similar = ({ uid }) => {
  const [kind, setKind] = useState("similar");
  const { data = [] } = useGet(["analysis-similar", uid, kind], `/analysis/similar/${uid}`, { kind });
  return (
    <div data-testid="dossier-similar"><div className="seg" style={{ marginBottom: 8 }}>{[["similar", "Similar"], ["cheaper", "Cheaper (≤60%)"], ["younger", "Younger"]].map(([k, l]) =>
      <button key={k} className={kind === k ? "on" : ""} onClick={() => setKind(k)} data-testid={`dossier-similar-${k}`}>{l}</button>)}</div>
      {!data.length && <p className="note">Nobody fits that yet.</p>}
      {data.map((p) => <div key={p.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => openDossier(p.unique_id)} data-testid={`dossier-sim-${p.unique_id}`}>
        <div style={{ flex: 1 }}><b>{p.name}</b><small>{p.club} · {p.age} · {money(p.est_value)}</small></div><span className="st n">{p.similarity}% alike</span></div>)}
    </div>
  );
};

const Body = ({ d, addCompare }) => (
  <div style={{ display: "grid", gap: 16, marginTop: 12 }}>
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><span className="st n">{d.club}</span><span className="st n">{d.league}</span><span className="st n">{d.nationality}</span><span className="st n">Age {d.age}</span>
      <button className="btn" onClick={addCompare} data-testid="dossier-compare-add"><GitCompare size={13} />Add to compare</button></div>
    <div className="card" data-testid="dossier-value"><div className="ttl">Estimated value: {money(d.est_value)}</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{d.value_factors.map((f) => <span key={f.name} className="st n" style={{ color: f.pct > 0 ? "#34D399" : f.pct < 0 ? "#FF6E6E" : undefined }} data-testid={`dossier-factor-${f.name}`}>{f.name} {f.pct > 0 ? "+" : ""}{f.pct}%</span>)}</div>
      {d.value_history.length > 1 && <div style={{ height: 140, marginTop: 10 }} data-testid="dossier-value-chart"><ResponsiveContainer><LineChart data={d.value_history}><XAxis dataKey="month" fontSize={10} /><YAxis tickFormatter={money} fontSize={10} width={52} /><Tooltip formatter={money} /><Line dataKey="value" stroke="#4C8DFF" dot={false} /></LineChart></ResponsiveContainer></div>}
      {d.value_history.length <= 1 && <small className="note">Value over time fills in as FMCC reads more saves.</small>}</div>
    <div className="card" data-testid="dossier-contract"><div className="ttl">Contract</div><p className="note" style={{ margin: 0 }}>Wage {money(d.wage)}/week · ends {d.contract_end || "—"}{d.release_clause ? ` · release clause ${money(d.release_clause)}` : ""}{d.loan ? ` · on loan from ${d.loan}` : ""}</p>
      <p className="note" style={{ margin: "4px 0 0" }}>This season: {d.appearances || 0} apps · {d.goals || 0} goals · {d.assists || 0} assists · {d.minutes || 0} min · rating {d.avg_rating ?? "—"}</p></div>
    <div className="card" data-testid="dossier-positions"><div className="ttl">Positions</div><div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{(d.positions || []).map((p, i) => <span key={p} className={`st ${i ? "n" : "g"}`}>{p}</span>)}</div></div>
    <div className="card" data-testid="dossier-roles"><div className="ttl">Top role fits</div>
      {d.roles.slice(0, 6).map((r) => <div key={r.role} className="row"><div style={{ flex: 1 }}><b>{r.name}</b><small>{r.natural ? "Natural position" : "Not his position"} · with ball {r.with_ball != null ? `${r.with_ball}%` : "—"} · without {r.without_ball != null ? `${r.without_ball}%` : "—"}</small></div><span className="mono">{r.fit}%</span></div>)}</div>
    <div className="card" data-testid="dossier-attributes"><div className="ttl">Attributes</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(150px,1fr))", gap: "4px 12px" }}>{Object.entries(d.attributes).map(([k, v]) => <div key={k} className="note" style={{ display: "flex", justifyContent: "space-between" }}>{k.replace(/_/g, " ")}<b style={{ color: band(v) }}>{v}</b></div>)}</div></div>
    <div className="card"><div className="ttl">Find another</div><Similar uid={d.unique_id} /></div>
  </div>
);

const Compare = ({ ids, close, remove }) => {
  const { data: t } = useGet("analysis-table", "/analysis/table");
  const ps = (t?.rows || []).filter((r) => ids.includes(r.unique_id));
  const max = Object.fromEntries(RADAR.map((k) => [k, Math.max(0.01, ...(t?.rows || []).map((r) => r.p90?.[k] || 0))]));
  const data = RADAR.map((k) => ({ k: NAMES[k], ...Object.fromEntries(ps.map((p) => [p.name, Math.round(((p.p90?.[k] || 0) / max[k]) * 100)])) }));
  return (
    <Dialog open={ids.length > 0 && !!t} onOpenChange={(o) => !o && close()}>
      <DialogContent style={{ maxWidth: 900 }} data-testid="compare-dialog"><DialogHeader><DialogTitle>Compare players</DialogTitle></DialogHeader>
        <div style={{ height: 300 }}><ResponsiveContainer><RadarChart data={data}><PolarGrid /><PolarAngleAxis dataKey="k" fontSize={11} />{ps.map((p, i) => <Radar key={p.unique_id} name={p.name} dataKey={p.name} stroke={COLORS[i]} fill={COLORS[i]} fillOpacity={0.15} />)}<Legend /></RadarChart></ResponsiveContainer></div>
        <div style={{ overflowX: "auto" }}><table className="tbl"><thead><tr><th></th>{ps.map((p) => <th key={p.unique_id}>{p.name} <button className="ib" onClick={() => remove(p.unique_id)} data-testid={`compare-remove-${p.unique_id}`}><X size={11} /></button></th>)}</tr></thead>
          <tbody>{[["Est. value", (p) => money(p.est_value)], ["Best role", (p) => `${p.top_roles?.[0]?.name || "—"} ${p.role_fit}%`], ["Age", (p) => p.age], ...RADAR.map((k) => [`${NAMES[k]} / 90`, (p) => p.p90?.[k]?.toFixed?.(2) ?? "—"])].map(([l, fn]) =>
            <tr key={l} style={{ cursor: "default" }}><td><b>{l}</b></td>{ps.map((p) => <td key={p.unique_id} className="mono">{fn(p)}</td>)}</tr>)}</tbody></table></div>
      </DialogContent>
    </Dialog>
  );
};

export const DossierHost = () => {
  const [uid, setUid] = useState(null);
  const [cmp, setCmp] = useState([]);
  const [showCmp, setShowCmp] = useState(false);
  useEffect(() => { const h = (e) => setUid(e.detail); window.addEventListener("fmcc-dossier", h); return () => window.removeEventListener("fmcc-dossier", h); }, []);
  const { data: d } = useGet(["analysis-player", uid], `/analysis/player/${uid}`, undefined, { enabled: !!uid });
  return (
    <>
      <Sheet open={!!uid} onOpenChange={(o) => !o && setUid(null)}>
        <SheetContent side="right" className="dossier-sheet" data-testid="dossier-sheet">
          <SheetHeader><SheetTitle data-testid="dossier-name">{d?.name || "Loading…"}</SheetTitle><SheetDescription>{d ? `${(d.positions || []).join(", ")} · Player dossier` : ""}</SheetDescription></SheetHeader>
          {d && d.unique_id === uid && <Body d={d} addCompare={() => { setCmp((c) => [...new Set([...c, uid])].slice(-5)); setShowCmp(true); }} />}
        </SheetContent>
      </Sheet>
      {showCmp && <Compare ids={cmp} close={() => setShowCmp(false)} remove={(id) => setCmp((c) => c.filter((x) => x !== id))} />}
    </>
  );
};
