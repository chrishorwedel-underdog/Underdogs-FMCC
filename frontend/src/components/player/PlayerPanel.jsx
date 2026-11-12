import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Sparkles, Star, Scale, FlaskConical, ListPlus, Users } from "lucide-react";
import { toast } from "sonner";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { api, gameDate } from "@/lib/api";
import { useGet, useAct, TabBar } from "@/lib/ui";
import { usePersist, returnToRow } from "@/lib/remember";
import { sendToFm } from "@/lib/fmShortlist";
import { WatchButton } from "@/components/WatchButton";
import { Empty } from "@/components/Empty";
import { Loading } from "@/components/Loading";
import { ScoutCtx, fmtMoney, fmtWage, pctColor, ContractTag } from "@/components/scout/ctx";
import { Replacement, PriceExplained, HistoryChart } from "@/components/scout/Lab";
import { ProfileLab } from "@/components/scout/Recruit";
import { RadarCard, AttrHeatmap, MetricHeatmap, attributeRadar } from "@/components/charts/DataHub";
import { SquadRadars } from "@/components/squad/SquadRadars";
import { addTrial } from "@/components/squad/TryXI";
import { money } from "@/components/analysis/StatsTable";

const TABS = [["overview", "Overview"], ["stats", "Stats"], ["radar", "Radar & heatmap"], ["contract", "Contract & value"], ["history", "History"]];
const XY = { GK: [50, 90], "D (C)": [50, 74], "D (L)": [14, 70], "D (R)": [86, 70], "WB (L)": [12, 56], "WB (R)": [88, 56], DM: [50, 60],
  "M (C)": [50, 47], "AM (C)": [50, 32], "AM (L)": [18, 30], "AM (R)": [82, 30], ST: [50, 13] };

const MiniPitch = ({ positions }) => (
  <svg viewBox="0 0 100 100" width="120" height="120" data-testid="profile-pitch" style={{ background: "#0F2A1C", borderRadius: 8, flexShrink: 0 }}>
    <rect x="4" y="4" width="92" height="92" fill="none" stroke="rgba(255,255,255,.25)" /><line x1="4" y1="50" x2="96" y2="50" stroke="rgba(255,255,255,.25)" />
    {positions.map((p, i) => { const [x, y] = XY[p] || [50, 50]; return <circle key={p} cx={x} cy={y} r={i ? 4.5 : 6.5} fill={i ? "rgba(76,141,255,.55)" : "var(--acc)"} />; })}
  </svg>
);

const Pizza = ({ items }) => {
  const n = items.length;
  if (!n) return null;
  const arc = (i, r) => {
    const a0 = (i / n) * 2 * Math.PI - Math.PI / 2, a1 = ((i + 1) / n) * 2 * Math.PI - Math.PI / 2;
    return `M50,50 L${50 + r * Math.cos(a0)},${50 + r * Math.sin(a0)} A${r},${r} 0 0 1 ${50 + r * Math.cos(a1)},${50 + r * Math.sin(a1)} Z`;
  };
  return (
    <svg viewBox="0 0 100 100" width="210" height="210" data-testid="profile-pizza">
      {items.map((it, i) => <path key={it.k} d={arc(i, 46)} fill="rgba(255,255,255,.04)" stroke="var(--s1)" strokeWidth=".6" />)}
      {items.map((it, i) => <path key={`${it.k}v`} d={arc(i, 8 + (it.p / 100) * 38)} fill={pctColor(it.p)} opacity=".85" stroke="var(--s1)" strokeWidth=".6"><title>{`${it.label}: ${it.p}th percentile`}</title></path>)}
    </svg>
  );
};

const Similar = ({ uid, open }) => {
  const [kind, setKind] = useState("similar");
  const { data = [] } = useGet(["analysis-similar", uid, kind], `/analysis/similar/${uid}`, { kind });
  return (
    <div className="card" style={{ padding: 12 }} data-testid="dossier-similar"><div className="ttl">Find another</div>
      <div className="seg" style={{ margin: "6px 0 8px" }}>{[["similar", "Similar"], ["cheaper", "Cheaper (≤60%)"], ["younger", "Younger"]].map(([k, l]) =>
        <button key={k} className={kind === k ? "on" : ""} onClick={() => setKind(k)} data-testid={`dossier-similar-${k}`}>{l}</button>)}</div>
      {!data.length && <p className="note">Nobody fits that yet.</p>}
      {data.map((x) => <div key={x.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => open(x.unique_id)} data-testid={`dossier-sim-${x.unique_id}`}>
        <div style={{ flex: 1 }}><b>{x.name}</b><small>{x.club} · {x.age} · {money(x.est_value)}</small></div><span className="st n">{x.similarity}% alike</span></div>)}
    </div>
  );
};

const Actions = ({ p, close }) => {
  const act = useAct();
  const nav = useNavigate();
  const [, setCompare] = usePersist("scout-compare", []);
  const compare = () => { setCompare((c) => [...c.filter((x) => x !== p.unique_id), p.unique_id].slice(-4)); close(); nav("/scouting?tab=compare"); toast.success(`${p.name} added to Compare (up to four players)`); };
  return (
    <div className="pp-actions" data-testid="player-panel-actions">
      {p.source !== "html" && <WatchButton uid={p.unique_id} name={p.name} id="profile-watch" />}
      {!p.own && <button className="btn" title="Shortlist: players you're considering signing" onClick={() => act(() => api.post("/scouting/shortlist", { unique_id: p.unique_id, action: "add" }), "Added to shortlist", ["rankings"])} data-testid="profile-shortlist"><Star size={13} />Shortlist</button>}
      <button className="btn" onClick={compare} data-testid="profile-compare"><Scale size={13} />Compare</button>
      {!p.own && <button className="btn" onClick={() => toast.success(addTrial(p.unique_id) ? `${p.name} added to Try in XI (the oldest trial player was taken out; 3 at most)` : `${p.name} added to Try in XI on the Squad page`)} data-testid="dossier-try-xi"><FlaskConical size={13} />Try in XI</button>}
      {!p.own && p.source === "save" && <button className="btn" onClick={() => sendToFm(act, [p.unique_id])} data-testid="dossier-send-fm"><ListPlus size={13} />Send to FM shortlist</button>}
      {p.own && <button className="btn" onClick={() => { close(); nav("/squad"); }} data-testid="player-panel-open-squad"><Users size={13} />Open in Squad</button>}
    </div>
  );
};

const Overview = ({ p, d, s }) => {
  const act = useAct();
  const [busy, setBusy] = useState(false);
  const { prefs } = useScoutPrefs();
  const dof = async () => { setBusy(true); await act(() => api.post(`/scout/player/${p.unique_id}/dof-report`), "Report written", ["scout-player"]); setBusy(false); };
  const roles = s?.role_ratings?.length ? s.role_ratings : null;
  return <>
    <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
      <MiniPitch positions={p.positions || []} />
      <div style={{ fontSize: 13, color: "var(--mut)", lineHeight: 1.7 }}>
        <div>{p.age} · {p.nationality} · {p.club} ({p.league})<ContractTag m={p.months_left} />{p.league_scored === false && <span className="tag st a" title={p.league_note} data-testid="profile-noscore">No strength score</span>}</div>
        <div>Value <b className="mono" style={{ color: "var(--text)" }}>{fmtMoney(p.value, prefs)}</b> · wage <span className="mono">{fmtWage(p.wage, prefs)}</span></div>
        <div data-testid="profile-grade">Grade {p.grade_global ?? "—"} global · {p.grade_local ?? "—"} local · league ×{p.league_mult}
          {p.league && <a style={{ marginLeft: 8, color: "var(--acc)" }} href={`/scouting?tab=leagues&from=${encodeURIComponent(p.league)}${p.grade_local != null ? `&grade=${p.grade_local}` : ""}`} data-testid="profile-compare-league">Compare his league</a>}</div>
        {p.league_scored === false && <small style={{ display: "block", color: "var(--amb)" }} data-testid="profile-noscore-note">{p.league_note}</small>}
        {p.best_role && <div>Best role: {p.best_role}</div>}
      </div>
    </div>
    {d && <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }} data-testid="dossier-positions">{(d.positions || []).map((x, i) => <span key={x} className={`st ${i ? "n" : "g"}`}>{x}</span>)}</div>}
    {p.report && <p className="note" style={{ lineHeight: 1.6 }} data-testid="profile-report">{p.report}</p>}
    <button className="btn" style={{ justifySelf: "start" }} disabled={busy || !Object.keys(p.pct || {}).length} onClick={dof} data-testid="profile-dof-report"><Sparkles size={13} />{busy ? "Writing…" : "DOF report from the numbers"}</button>
    {p.dof_reports?.map((r) => <div key={r.id} className="soon" style={{ marginTop: 0 }} data-testid="profile-dof-text"><b>Director of Football</b> · {r.season}<br />{r.text}</div>)}
    {roles ? <div className="card" style={{ padding: 14 }} data-testid="player-sheet-roles"><div className="ttl" style={{ marginBottom: 6 }}>Role ratings</div>
      <div className="mbars">{roles.map((r) => <div className="mb" key={r.role} style={{ gridTemplateColumns: "170px 1fr 30px" }}><span>{r.name} ({r.duty})</span>
        <div className="track"><i style={{ width: `${r.rating}%`, background: r.natural ? "var(--acc)" : "var(--mut)" }} /></div><span className="mono">{r.rating}</span></div>)}</div></div>
      : d?.roles?.length > 0 && <div className="card" data-testid="dossier-roles"><div className="ttl">Top role fits</div>
        {d.roles.slice(0, 6).map((r) => <div key={r.role} className="row"><div style={{ flex: 1 }}><b>{r.name}</b><small>{r.natural ? "Natural position" : "Not his position"} · with ball {r.with_ball != null ? `${r.with_ball}%` : "—"} · without {r.without_ball != null ? `${r.without_ball}%` : "—"}</small></div><span className="mono">{r.fit}%</span></div>)}</div>}
  </>;
};

const Stats = ({ p, d, view, toggleCompare }) => {
  const pizza = (p.profile_keys || []).filter((k) => p.pct?.[k] != null).map((k) => ({ k, p: p.pct[k], label: p.labels[k] }));
  return <>
    {d && <p className="note" style={{ margin: 0 }} data-testid="dossier-season">This season: {d.appearances || 0} apps · {d.goals || 0} goals · {d.assists || 0} assists · {d.minutes || 0} min · rating {d.avg_rating ?? "—"}</p>}
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      <Pizza items={pizza} />
      <div style={{ flex: 1, minWidth: 220 }} data-testid="profile-phases">
        {Object.keys(p.phases || {}).length >= 3 && <RadarCard id="profile-phases-radar" title="Phases of play (percentile)" data={Object.entries(p.phases).map(([k, v]) => ({ axis: k.replace(/^\w/, (c) => c.toUpperCase()), value: v ?? 0 }))} height={220} />}
        {!pizza.length && <Empty id="profile-empty-pct" reason="minutes" text={`He has ${p.minutes} minutes. Percentiles and the radar need ${p.min_minutes || 400}; check back after a few more games.`} />}</div>
    </div>
    {pizza.length > 0 && <MetricHeatmap id="profile-metric-heatmap" title="Key stats heatmap (percentile vs his position)" rows={[{ name: p.name, values: Object.fromEntries(pizza.map((x) => [x.k, x.p])) }]} cols={pizza.map((x) => x.k)} label={p.labels} />}
    <ProfileLab uid={p.unique_id} view={view} onCompare={toggleCompare} />
    <Replacement uid={p.unique_id} />
  </>;
};

const RadarTab = ({ p, view }) => <>
  {view !== "moneyball" && p.attributes && <div className="hub-row" data-testid="profile-attributes">
    <RadarCard id="profile-attr-radar" title={`Attributes by area${view === "fair" ? ` · scout knowledge ${p.knowledge}%` : ""}`} data={attributeRadar(p.attributes)} max={20} height={240} />
    <AttrHeatmap id="profile-attr-heat" title="Attributes" attrs={p.attributes} /></div>}
  {view === "full" && p.hidden && <AttrHeatmap id="profile-hidden" title={`Hidden attributes · ${p.personality}`} attrs={p.hidden} />}
  {p.own && <SquadRadars uid={p.unique_id} />}
  {view === "moneyball" && !p.own && <Empty id="profile-moneyball-attrs" reason="missing" text="Moneyball view uses match stats and price only, so attributes are switched off. Switch the view in Scout Players to see them." />}
</>;

const Contract = ({ p, d, view }) => {
  const { prefs } = useScoutPrefs();
  return <>
    <div data-testid="profile-fair-price" className="note">Fair price <b className="mono" style={{ color: "var(--acc)" }}>{p.fair_price ? fmtMoney(p.fair_price, prefs) : "Not enough minutes"}</b> · confidence <span className={`st ${p.confidence === "High" ? "ok" : p.confidence === "Medium" ? "a" : "r"}`} data-testid="profile-confidence">{p.confidence}</span></div>
    {d && <div className="card" data-testid="dossier-value"><div className="ttl">Estimated value: {money(d.est_value)}</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{d.value_factors.map((f) => <span key={f.name} className="st n" style={{ color: f.pct > 0 ? "#34D399" : f.pct < 0 ? "#FF6E6E" : undefined }} data-testid={`dossier-factor-${f.name}`}>{f.name} {f.pct > 0 ? "+" : ""}{f.pct}%</span>)}</div>
      {d.value_history.length > 1 ? <div style={{ height: 140, marginTop: 10 }} data-testid="dossier-value-chart"><ResponsiveContainer><LineChart data={d.value_history}><XAxis dataKey="month" fontSize={10} /><YAxis tickFormatter={money} fontSize={10} width={52} /><Tooltip formatter={money} /><Line dataKey="value" stroke="#4C8DFF" dot={false} /></LineChart></ResponsiveContainer></div>
        : <small className="note">Value over time fills in as FMCC reads more saves.</small>}</div>}
    {d && <div className="card" data-testid="dossier-contract"><div className="ttl">Contract</div><p className="note" style={{ margin: 0 }}>Wage {money(d.wage)}/week · ends {d.contract_end || "—"}{d.release_clause ? ` · release clause ${money(d.release_clause)}` : ""}{d.loan ? ` · on loan from ${d.loan}` : ""}</p></div>}
    {!p.own && <PriceExplained uid={p.unique_id} view={view} />}
  </>;
};

const History = ({ p, s, open }) => <>
  {s?.identity && <p className="note" style={{ margin: 0 }} data-testid="player-sheet-uid">Game ID <span className="mono">{p.unique_id}</span> · first seen {gameDate(s.identity.first_seen_date)} · matched across saves by this ID</p>}
  {s?.history?.length > 0 && <div className="card" style={{ padding: 14 }}><div className="ttl" style={{ marginBottom: 10 }}>Ability gained across saves</div>
    <div style={{ height: 180 }} data-testid="player-sheet-chart"><ResponsiveContainer>
      <LineChart data={s.history.map((h) => ({ gain: h.ca - s.history[0].ca, label: gameDate(h.game_date, { month: "short" }) }))}>
        <XAxis dataKey="label" stroke="#5C626C" fontSize={11} tickLine={false} /><YAxis stroke="#5C626C" fontSize={11} domain={["dataMin - 3", "dataMax + 3"]} width={32} tickLine={false} />
        <Tooltip contentStyle={{ background: "#121519", border: "1px solid rgba(255,255,255,.13)", borderRadius: 10, fontSize: 12 }} />
        <Line type="monotone" dataKey="gain" name="Ability gained" stroke="#4C8DFF" strokeWidth={2} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div></div>}
  {p.seasons?.length > 0 && <div className="card" style={{ padding: 12 }} data-testid="profile-seasons"><div className="ttl">Seasons in this career</div><HistoryChart seasons={p.seasons} />
    <table className="tbl"><thead><tr><th>Season</th><th>Club</th><th>Mins</th><th>Grade</th><th>npxG/90</th><th>xA/90</th></tr></thead>
      <tbody>{p.seasons.map((x) => <tr key={x.season}><td>{x.season}</td><td>{x.club}</td><td className="mono">{x.minutes}</td><td className="mono">{x.grade ?? "—"}</td><td className="mono">{x.p90?.npxg ?? "—"}</td><td className="mono">{x.p90?.xa ?? "—"}</td></tr>)}</tbody></table></div>}
  <div className="card" style={{ padding: 12 }} data-testid="profile-similar"><div className="ttl">Similar players</div>
    {p.similar.map((x) => <div key={x.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => open(x.unique_id)} data-testid={`similar-${x.unique_id}`}>
      <div style={{ flex: 1 }}>{x.name}<small>{x.club} · {x.age} · grade {x.grade}</small></div><span className="mono" title={`Style ${x.style} · ability ${x.ability}`}>{x.similarity}%</span></div>)}
    {!p.similar.length && <p className="note">Not enough match data to compare styles.</p>}</div>
  <Similar uid={p.unique_id} open={open} />
</>;

const useScoutPrefs = () => {
  const { data } = useGet("scout-prefs", "/scout/prefs");
  return { prefs: data || { currency: "GBP", wages: "week" } };
};

export const openPlayer = (uid) => window.dispatchEvent(new CustomEvent("fmcc-dossier", { detail: uid }));

export const PlayerPanelHost = () => {
  const [params, setParams] = useSearchParams();
  const [uid, setUid] = useState(null);
  const [tab, setTab] = useState("overview");
  const [view] = usePersist("scout-view", "full");
  const [compare, setCompare] = usePersist("scout-compare", []);
  const { prefs } = useScoutPrefs();
  const q = Number(params.get("player")) || null;
  useEffect(() => { if (q) { setUid(q); } }, [q]);
  useEffect(() => { const h = (e) => { setUid(e.detail); setTab("overview"); }; window.addEventListener("fmcc-dossier", h); return () => window.removeEventListener("fmcc-dossier", h); }, []);
  const { data: p } = useGet("scout-player", `/scout/player/${uid}`, { view, uid }, { enabled: !!uid });
  const { data: d } = useGet(["analysis-player", uid], `/analysis/player/${uid}`, undefined, { enabled: !!uid, retry: false });
  const { data: s } = useQuery({ queryKey: ["player", uid], queryFn: () => api.get(`/players/${uid}`).then((r) => r.data), enabled: !!uid && !!p?.own, retry: false });
  const close = () => { const u = uid; setUid(null); if (params.get("player")) { params.delete("player"); setParams(params, { replace: true }); } if (u) { returnToRow(u); } };
  const open = (id) => { setUid(id); setTab("overview"); };
  const toggleCompare = (id) => setCompare((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id].slice(-4)));
  const ready = p && p.unique_id === uid;
  return (
    <ScoutCtx.Provider value={{ view, prefs, openPlayer: open, compare, toggleCompare }}>
      <Sheet open={!!uid} onOpenChange={(o) => !o && close()}>
        <SheetContent side="right" className="overflow-y-auto pp-sheet" style={{ background: "var(--s1)", borderColor: "var(--line)" }} data-testid="player-panel">
          <SheetHeader><SheetTitle style={{ color: "var(--text)" }} data-testid="player-panel-name">{ready ? p.name : <span className="skel" style={{ display: "inline-block", width: 160, height: 18, verticalAlign: "middle" }} aria-label="Loading" />}{ready && <span className="tag st n">{p.cohort}</span>}</SheetTitle>
            <SheetDescription>{ready ? `${(p.positions || []).join(", ")} · ${p.club}${p.own ? " · your player" : ""}` : ""}</SheetDescription></SheetHeader>
          {!ready ? <Loading id="player-panel-loading" rows={6} label="Loading player" /> : <div style={{ display: "grid", gap: 14, marginTop: 10, gridTemplateColumns: "minmax(0,1fr)" }}>
            <Actions p={p} close={close} />
            <div style={{ overflowX: "auto" }}><TabBar id="player-panel" value={tab} onChange={setTab} tabs={TABS} /></div>
            {tab === "overview" && <Overview p={p} d={d} s={s} />}
            {tab === "stats" && <Stats p={p} d={d} view={view} toggleCompare={toggleCompare} />}
            {tab === "radar" && <RadarTab p={p} view={view} />}
            {tab === "contract" && <Contract p={p} d={d} view={view} />}
            {tab === "history" && <History p={p} s={s} open={open} />}
          </div>}
        </SheetContent>
      </Sheet>
    </ScoutCtx.Provider>
  );
};
