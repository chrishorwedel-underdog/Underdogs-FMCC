import { useState } from "react";
import { Sparkles, Star, Scale } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { Quadrant, Replacement, PriceExplained, HistoryChart } from "./Lab";
import { ProfileLab } from "./Recruit";
import { useScout, fmtMoney, fmtWage, pctColor, ContractTag } from "./ctx";
import { RadarCard, AttrHeatmap, MetricHeatmap, attributeRadar } from "@/components/charts/DataHub";
import { Empty } from "@/components/Empty";

const XY = { GK: [50, 90], "D (C)": [50, 74], "D (L)": [14, 70], "D (R)": [86, 70], "WB (L)": [12, 56], "WB (R)": [88, 56], DM: [50, 60],
  "M (C)": [50, 47], "AM (C)": [50, 32], "AM (L)": [18, 30], "AM (R)": [82, 30], ST: [50, 13] };

const MiniPitch = ({ positions }) => (
  <svg viewBox="0 0 100 100" width="120" height="120" data-testid="profile-pitch" style={{ background: "#0F2A1C", borderRadius: 8 }}>
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

const Body = ({ p, view }) => {
  const { prefs, openPlayer, compare, toggleCompare } = useScout();
  const act = useAct();
  const [busy, setBusy] = useState(false);
  const pizza = (p.profile_keys || []).filter((k) => p.pct?.[k] != null).map((k) => ({ k, p: p.pct[k], label: p.labels[k] }));
  const dof = async () => { setBusy(true); await act(() => api.post(`/scout/player/${p.unique_id}/dof-report`), "Report written", ["scout-player"]); setBusy(false); };
  return (
    <div style={{ display: "grid", gap: 14, marginTop: 10 }}>
      <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
        <MiniPitch positions={p.positions || []} />
        <div style={{ fontSize: 13, color: "var(--mut)", lineHeight: 1.7 }}>
          <div>{p.age} · {p.nationality} · {p.club} ({p.league})<ContractTag m={p.months_left} />{p.league_scored === false && <span className="tag st a" title={p.league_note} data-testid="profile-noscore">No strength score</span>}</div>
          <div>Value <b className="mono" style={{ color: "var(--text)" }}>{fmtMoney(p.value, prefs)}</b> · wage <span className="mono">{fmtWage(p.wage, prefs)}</span></div>
          <div data-testid="profile-fair-price">Fair price <b className="mono" style={{ color: "var(--acc)" }}>{p.fair_price ? fmtMoney(p.fair_price, prefs) : "Not enough minutes"}</b> · confidence <span className={`st ${p.confidence === "High" ? "ok" : p.confidence === "Medium" ? "a" : "r"}`} data-testid="profile-confidence">{p.confidence}</span></div>
          <div data-testid="profile-grade">Grade {p.grade_global ?? "—"} global · {p.grade_local ?? "—"} local · league ×{p.league_mult}
            {p.league && <a style={{ marginLeft: 8, color: "var(--acc)" }} href={`/scouting?tab=leagues&from=${encodeURIComponent(p.league)}${p.grade_local != null ? `&grade=${p.grade_local}` : ""}`} data-testid="profile-compare-league">Compare his league</a>}</div>
          {p.league_scored === false && <small style={{ display: "block", color: "var(--amb)" }} data-testid="profile-noscore-note">{p.league_note}</small>}
          {p.best_role && <div>Best role: {p.best_role}</div>}
          {p.contract_end && <div>Contract until {p.contract_end}</div>}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {!p.own && <button className="btn" onClick={() => act(() => api.post("/scouting/shortlist", { unique_id: p.unique_id, action: "add" }), "Added to shortlist", ["rankings"])} data-testid="profile-shortlist"><Star size={13} />Shortlist</button>}
        <button className={`btn${compare.includes(p.unique_id) ? " btn-p" : ""}`} onClick={() => toggleCompare(p.unique_id)} data-testid="profile-compare"><Scale size={13} />Compare</button>
        <button className="btn" disabled={busy || !pizza.length} onClick={dof} data-testid="profile-dof-report"><Sparkles size={13} />{busy ? "Writing…" : "DOF report from the numbers"}</button>
      </div>
      {p.report && <p className="note" style={{ lineHeight: 1.6 }} data-testid="profile-report">{p.report}</p>}
      <ProfileLab uid={p.unique_id} view={view} onCompare={toggleCompare} />
      <Replacement uid={p.unique_id} />
      <PriceExplained uid={p.unique_id} view={view} />
      {p.dof_reports?.map((r) => <div key={r.id} className="soon" style={{ marginTop: 0 }} data-testid="profile-dof-text"><b>Director of Football</b> · {r.season}<br />{r.text}</div>)}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <Pizza items={pizza} />
        <div style={{ flex: 1, minWidth: 220 }} data-testid="profile-phases">
          {Object.keys(p.phases || {}).length >= 3 && <RadarCard id="profile-phases-radar" title="Phases of play (percentile)" data={Object.entries(p.phases).map(([k, v]) => ({ axis: k.replace(/^\w/, (c) => c.toUpperCase()), value: v ?? 0 }))} height={220} />}
          {!pizza.length && <Empty id="profile-empty-pct" reason="minutes" text={`He has ${p.minutes} minutes. Percentiles and the radar need ${p.min_minutes || 400}; check back after a few more games.`} />}</div>
      </div>
      {pizza.length > 0 && <MetricHeatmap id="profile-metric-heatmap" title="Key stats heatmap (percentile vs his position)" rows={[{ name: p.name, values: Object.fromEntries(pizza.map((x) => [x.k, x.p])) }]} cols={pizza.map((x) => x.k)} label={p.labels} />}
      {view !== "moneyball" && p.attributes && <div className="hub-row" data-testid="profile-attributes">
        <RadarCard id="profile-attr-radar" title={`Attributes by area${view === "fair" ? ` · scout knowledge ${p.knowledge}%` : ""}`} data={attributeRadar(p.attributes)} max={20} height={240} />
        <AttrHeatmap id="profile-attr-heat" title="Attributes" attrs={p.attributes} /></div>}
      {view === "full" && p.hidden && <AttrHeatmap id="profile-hidden" title={`Hidden attributes · ${p.personality}`} attrs={p.hidden} />}
      {p.role_ratings?.length > 0 && <div className="note">Roles: {p.role_ratings.map((r) => `${r.name} (${r.duty}) ${r.rating}`).join(" · ")}</div>}
      <div className="card" style={{ padding: 12 }} data-testid="profile-similar"><div className="ttl">Similar players</div>
        {p.similar.map((s) => <div key={s.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => openPlayer(s.unique_id)} data-testid={`similar-${s.unique_id}`}>
          <div style={{ flex: 1 }}>{s.name}<small>{s.club} · {s.age} · grade {s.grade}</small></div><span className="mono" title={`Style ${s.style} · ability ${s.ability}`}>{s.similarity}%</span><span className="mono" style={{ width: 70, textAlign: "right" }}>{fmtMoney(s.value, prefs)}</span></div>)}
        {!p.similar.length && <p className="note">Not enough match data to compare styles.</p>}</div>
      {p.seasons?.length > 0 && <div className="card" style={{ padding: 12 }} data-testid="profile-seasons"><div className="ttl">Seasons in this career</div><HistoryChart seasons={p.seasons} />
        <table className="tbl"><thead><tr><th>Season</th><th>Club</th><th>Mins</th><th>Grade</th><th>npxG/90</th><th>xA/90</th></tr></thead>
          <tbody>{p.seasons.map((s) => <tr key={s.season}><td>{s.season}</td><td>{s.club}</td><td className="mono">{s.minutes}</td><td className="mono">{s.grade ?? "—"}</td><td className="mono">{s.p90?.npxg ?? "—"}</td><td className="mono">{s.p90?.xa ?? "—"}</td></tr>)}</tbody></table></div>}
    </div>
  );
};

export const ProfileSheet = ({ uid, onClose }) => {
  const { view } = useScout();
  const { data } = useGet("scout-player", `/scout/player/${uid}`, { view, uid }, { enabled: !!uid });
  return (
    <Sheet open={!!uid} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="right" className="overflow-y-auto" style={{ width: 620, maxWidth: "100vw", background: "var(--s1)", borderColor: "var(--line)" }} data-testid="profile-sheet">
        <SheetHeader><SheetTitle style={{ color: "var(--text)" }} data-testid="profile-name">{data?.name || "Loading…"}<span className="tag st n">{data?.cohort}</span></SheetTitle></SheetHeader>
        {data && data.unique_id === uid && <Body p={data} view={view} />}
      </SheetContent>
    </Sheet>
  );
};
