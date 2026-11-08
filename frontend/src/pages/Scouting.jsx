import { useState } from "react";
import { Star, Scale } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { ScoutCtx, useScout, fmtMoney } from "@/components/scout/ctx";
import { PlayersTab } from "@/components/scout/PlayersTab";
import { ProfileSheet } from "@/components/scout/ProfileSheet";
import { MyClubTab, DealsTab } from "@/components/scout/ClubDeals";
import { ScatterTab, Breakdown } from "@/components/scout/Charts";
import { ComputedTab, RoleScoresTab } from "@/components/scout/Computed";
import { LeaguesTab } from "@/components/scout/LeaguesTab";
import { FormulasTab, Quadrant } from "@/components/scout/Lab";
import { PossessionTab, ImportTab } from "@/components/scout/DataTabs";

const Shortlist = ({ open }) => {
  const { data } = useGet("rankings", "/scouting/rankings", { shortlist_only: true, sort: "score" });
  const { prefs } = useScout();
  const act = useAct();
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }}>
      <table className="tbl" data-testid="rankings-table">
        <thead><tr><th></th><th>Player</th><th>Age</th><th>Club</th><th>Best role</th><th>Value</th><th>Score</th></tr></thead>
        <tbody>{data?.rows.map((r) => (
          <tr key={r.unique_id} onClick={() => open(r.unique_id)} data-testid={`ranking-row-${r.unique_id}`}>
            <td onClick={(e) => e.stopPropagation()}><button className="ib" style={{ width: 28, height: 28, color: "var(--amb)" }} onClick={() => act(() => api.post("/scouting/shortlist", { unique_id: r.unique_id, action: "remove" }), "Removed from shortlist", ["rankings"])} data-testid={`shortlist-toggle-${r.unique_id}`}><Star size={14} fill="currentColor" /></button></td>
            <td><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.nationality} · {r.positions.join(", ")}</small></td><td>{r.age}</td><td>{r.club}</td><td>{r.best_role}</td><td className="mono">{fmtMoney(r.value, prefs)}</td><td className="mono" style={{ color: "var(--acc)" }}>{r.score}</td>
          </tr>))}</tbody>
      </table>
      {data && !data.rows.length && <p className="note" style={{ padding: 10 }}>Star players in the Players tab to shortlist them.</p>}
    </div>
  );
};

const CompareTable = ({ ids, clear }) => {
  const { view, prefs } = useScout();
  const { data = [] } = useGet("compare", "/scouting/compare", { ids: ids.filter((i) => i > 0).join(",") }, { enabled: ids.some((i) => i > 0) });
  const keys = data[0] && view === "full" ? Object.keys(data[0].attributes) : [];
  const money = (v) => fmtMoney(v, prefs);
  return (
    <div className="card" style={{ overflowX: "auto" }} data-testid="moneyball-compare">
      <div className="ttl">Side by side<span style={{ marginLeft: "auto" }} /><button className="btn" onClick={clear} data-testid="compare-clear">Clear</button></div>
      <table className="tbl" style={{ marginTop: 10 }}>
        <thead><tr><th></th>{data.map((p) => <th key={p.unique_id}>{p.name}</th>)}</tr></thead>
        <tbody>{[["Club", (p) => p.club], ["Age", (p) => p.age], ["Value", (p) => money(p.value)], ["Average rating", (p) => p.avg_rating ?? "—"], ["Value for money", (p) => p.vfm],
          ...(view === "full" ? [["Best roles", (p) => p.roles.map((r) => `${r.name} ${r.rating}`).join(" · ")]] : []), ...keys.map((k) => [k.replace(/_/g, " "), (p) => p.attributes[k]])].map(([l, fn]) => (
          <tr key={l} style={{ cursor: "default" }}><td style={{ color: "var(--mut)", textTransform: "capitalize" }}>{l}</td>{data.map((p) => <td key={p.unique_id} className="mono">{fn(p)}</td>)}</tr>))}</tbody>
      </table>
    </div>
  );
};

const ViewBar = ({ view, setView, prefs, setPrefs }) => (
  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
    <TabBar id="scout-view" value={view} onChange={setView} tabs={[["full", "Full"], ["fair", "Fair play"], ["moneyball", "Moneyball"]]} />
    <select className="inp" style={{ width: 80, height: 36 }} value={prefs.currency} onChange={(e) => setPrefs({ ...prefs, currency: e.target.value })} data-testid="pref-currency"><option value="GBP">£</option><option value="EUR">€</option><option value="USD">$</option></select>
    <select className="inp" style={{ width: 120, height: 36 }} value={prefs.wages} onChange={(e) => setPrefs({ ...prefs, wages: e.target.value })} data-testid="pref-wages"><option value="week">Per week</option><option value="month">Per month</option><option value="year">Per year</option></select>
  </div>
);

const VIEW_NOTE = { full: "Full: everything, including CA, PA, hidden attributes, personality and a written report.", fair: "Fair play: only what your scouts would show you in the game. Attributes are ranges, CA, PA and hidden attributes are off.",
  moneyball: "Moneyball: match stats and price only. Attributes are switched off." };

export default function Scouting({ initialTab = "players" }) {
  const [tab, setTab] = useState(initialTab);
  const [view, setView] = useState("full");
  const [compare, setCompare] = useState([]);
  const [open, setOpen] = useState(null);
  const { data: saved } = useGet("scout-prefs", "/scout/prefs");
  const act = useAct();
  const prefs = saved || { currency: "GBP", wages: "week" };
  const setPrefs = (p) => act(() => api.put("/scout/prefs", p), null, ["scout-prefs"]);
  const toggleCompare = (id) => setCompare((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id].slice(-4)));
  const tabs = [["players", "Players"], ["myclub", "My Club"], ["deals", "Deals & Offers"], ["scatter", "Scatter"], ["compare", `Compare${compare.length ? ` (${compare.length})` : ""}`],
    ["computed", "Computed stats"], ["formulas", "Formulas"], ["roles", "Role scores"], ["leagues", "Leagues"], ["possession", "Possession"], ["import", "HTML import"], ["shortlist", "Shortlist"], ["rules", "Rules"]];
  return (
    <ScoutCtx.Provider value={{ view, prefs, openPlayer: setOpen, compare, toggleCompare }}>
      <div data-testid="scouting-page">
        <PageHead eyebrow="ScoutSheet built in, with FMDataLab-style analytics" title={initialTab === "compare" ? "Moneyball" : "Scout Players"}>
          <ViewBar view={view} setView={setView} prefs={prefs} setPrefs={setPrefs} />
        </PageHead>
        <p className="note" style={{ marginBottom: 10 }} data-testid="scout-view-note"><Scale size={12} style={{ display: "inline", verticalAlign: -1 }} /> {VIEW_NOTE[view]}</p>
        <div style={{ overflowX: "auto", marginBottom: 16 }}><TabBar id="scouting" value={tab} onChange={setTab} tabs={tabs} /></div>
        {tab === "players" && <PlayersTab />}
        {tab === "myclub" && <MyClubTab />}
        {tab === "deals" && <><DealsTab /><Quadrant /></>}
        {tab === "formulas" && <FormulasTab />}
        {tab === "scatter" && <ScatterTab />}
        {tab === "compare" && (compare.length ? <><CompareTable ids={compare} clear={() => setCompare([])} /><Breakdown ids={compare} /></>
          : <div className="soon">Pick up to 4 players with the scales button in Players or in a profile to compare them here.</div>)}
        {tab === "computed" && <ComputedTab />}
        {tab === "roles" && <RoleScoresTab />}
        {tab === "leagues" && <LeaguesTab />}
        {tab === "possession" && <PossessionTab />}
        {tab === "import" && <ImportTab />}
        {tab === "shortlist" && <Shortlist open={setOpen} />}
        {tab === "rules" && <RulesTab module="scouting" title="Scouting and Moneyball rules" />}
        <ProfileSheet uid={open} onClose={() => setOpen(null)} />
      </div>
    </ScoutCtx.Provider>
  );
}
