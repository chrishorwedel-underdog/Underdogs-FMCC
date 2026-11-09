import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ArrowRight, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar } from "@/lib/ui";
import { Pitch } from "@/components/squad/Pitch";

const strengthOf = (slots, depth) => {
  const v = Object.entries(slots).map(([k, u]) => depth[k]?.find((r) => r.unique_id === u)?.rating || 0);
  return Math.round(v.reduce((a, b) => a + b, 0) / Math.max(1, v.length));
};

const Side = ({ plan, mode, slots }) => {
  const cur = strengthOf(slots, plan.depth);
  const why = mode === "custom" ? [["blu", "Your own lineup. Click any player on the pitch to swap him from the depth chart."]] : plan[mode].why;
  return (
    <div>
      <div className="card rise d2"><div className="ttl">Team strength</div>
        <div className="cmp">
          <div className="row">Best XI<div className="track"><i style={{ width: `${plan.best.strength}%`, background: "var(--mut)" }} /></div><span className="mono">{plan.best.strength}</span></div>
          <div className="row">This lineup<div className="track"><i style={{ width: `${cur}%`, background: "var(--acc)" }} /></div><span className="mono" style={{ color: "var(--acc)" }} data-testid="lineup-strength">{cur}</span></div>
        </div>
      </div>
      <div className="card rise d3" style={{ marginTop: 16 }}><div className="ttl">Why this lineup</div>
        <ul className="why" data-testid="lineup-why">{why.map(([c, t], i) => <li key={i}><i style={{ background: `var(--${c})`, boxShadow: `0 0 8px var(--${c})` }} />{t}</li>)}</ul>
      </div>
      <div className="card rise d4" style={{ marginTop: 16 }}><div className="ttl">Under-21 minutes this month</div>
        <div className="mbars" style={{ gap: 10 }}>
          {plan.youth_minutes.map((y) => (
            <div className="mb" key={y.unique_id} style={{ gridTemplateColumns: "110px 1fr 64px" }}><span>{y.name}</span>
              <div className="track" style={{ height: 7 }}><i style={{ width: `${Math.min(100, (y.month_minutes / plan.rules.target_minutes) * 100)}%`, background: y.month_minutes < plan.rules.target_minutes ? "var(--amb)" : "var(--acc)" }} /></div>
              <span className="mono">{y.month_minutes}/{plan.rules.target_minutes}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
};

const MODES = [["best", "Best XI"], ["dev", "Development XI"], ["domestic", "Domestic XI"], ["cup", "Cup XI"], ["uefa", "UEFA XI"]];
const readExtra = () => { try { return JSON.parse(localStorage.getItem("fmcc-extra-formations") || "[]").slice(0, 3); } catch { return []; } };

const Formations = ({ plan, formation, setFormation }) => {
  const [extra, setExtra] = useState(readExtra);
  const save = (next) => { setExtra(next); localStorage.setItem("fmcc-extra-formations", JSON.stringify(next)); };
  const tabs = [...Object.entries(plan.formations), ...extra.filter((k) => plan.all_formations[k]).map((k) => [k, plan.all_formations[k]])];
  const options = Object.entries(plan.all_formations).filter(([k]) => !plan.formations[k] && !extra.includes(k));
  const add = (k) => { if (k) { save([...extra, k]); setFormation(k); } };
  const remove = (k) => { save(extra.filter((x) => x !== k)); if (formation === k) setFormation(null); };
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }} data-testid="formation-picker">
      <TabBar id="formation" value={plan.formation.key} onChange={setFormation} tabs={tabs} />
      {plan.from_save && <small className="st g" data-testid="formation-from-save">Your tactics from the save</small>}
      {extra.map((k) => <button key={k} className="btn" style={{ height: 30, padding: "0 8px" }} title={`Remove ${plan.all_formations[k]}`} onClick={() => remove(k)} data-testid={`formation-remove-${k}`}><X size={12} />{plan.all_formations[k]}</button>)}
      {extra.length < 3 && <select className="inp" style={{ width: 190, height: 34 }} value="" onChange={(e) => add(e.target.value)} data-testid="formation-add-select">
        <option value="">+ Add a tactic ({3 - extra.length} left)</option>{options.map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select>}
    </div>
  );
};

export const LineupView = ({ formation, setFormation }) => {
  const { data: plan } = useGet("plan", "/squad/plan", { formation });
  const act = useAct();
  const [mode, setMode] = useState("dev");
  const [slots, setSlots] = useState({});
  useEffect(() => { if (plan) setSlots(plan[mode === "custom" ? "dev" : mode].slots); }, [plan, formation]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!plan) return <p className="note">Working out lineups…</p>;
  const switchMode = (m) => { setMode(m); if (m !== "custom") setSlots(plan[m].slots); };
  const pick = (key, uid) => {
    const other = Object.keys(slots).find((k) => slots[k] === uid);
    if (other === key) return;
    const next = { ...slots, [key]: uid };
    if (other) {
      if (!plan.depth[other].some((r) => r.unique_id === slots[key])) { toast.error(`${plan.players[slots[key]].name} can't play ${other}. Pick someone else.`); return; }
      next[other] = slots[key];
    }
    setSlots(next); setMode("custom");
  };
  const use = () => act(() => api.post("/lineups", { formation: plan.formation.key, kind: mode, slots, based_on_save_no: plan.save_no, expected_revision: plan.saved?.revision || 0 }),
    (d) => `Lineup saved (version ${d.revision})`, ["plan"]);
  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 18, alignItems: "center" }}>
        <TabBar id="lineup-mode" value={mode} onChange={switchMode} tabs={[...MODES, ...(mode === "custom" ? [["custom", "My changes"]] : [])]} />
        <Formations plan={plan} formation={formation} setFormation={setFormation} />
        {plan.saved && <span className="note" data-testid="lineup-saved-label">Saved: {plan.saved.name} · version {plan.saved.revision}</span>}
        <button className="btn btn-p btn-l" style={{ marginLeft: "auto" }} onClick={use} data-testid="use-lineup-button">Use this lineup <ArrowRight size={15} /></button>
      </div>
      <div className="sq"><Pitch plan={plan} slots={slots} onPick={pick} /><Side plan={plan} mode={mode} slots={slots} /></div>
    </div>
  );
};
