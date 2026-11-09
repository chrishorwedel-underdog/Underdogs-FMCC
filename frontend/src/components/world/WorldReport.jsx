import { useState } from "react";
import { Newspaper, Trophy, ArrowLeftRight, BarChart3, Table2, ArrowUp, ArrowDown, Pencil } from "lucide-react";
import { api, gameDate } from "@/lib/api";
import { useAct, useGet } from "@/lib/ui";

const money = (v) => (v >= 1e6 ? `€${(v / 1e6).toFixed(1)}m` : `€${Math.round(v / 1000)}k`);
const Who = ({ r }) => <><b style={{ color: "var(--text)" }}>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.age} · {r.club}</small></>;

const News = ({ d }) => (
  <div className="card" data-testid="world-news"><div className="ttl"><Newspaper size={14} />{d.scope ? `${d.scope}: top stories` : "The 12 biggest stories"}</div>
    {d.news.length ? <ol style={{ margin: "8px 0 0", paddingLeft: 20, display: "grid", gap: 6 }}>{d.news.map((n, i) => (
      <li key={i} data-testid={`world-news-${i}`}><span className="st n" style={{ marginRight: 6 }}>{n.tag}</span>{n.text}{!d.country && !d.league && <small style={{ color: "var(--dim)" }}> · {n.country}</small>}</li>))}</ol>
      : <p className="note">No big stories this month.</p>}
  </div>
);

const Awards = ({ d }) => (
  <div className="card" data-testid="world-awards"><div className="ttl"><Trophy size={14} />{d.scope ? `${d.scope}'s` : "World"} players of the month</div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(230px, 100%), 1fr))", gap: 12, marginTop: 8 }}>
      {Object.entries(d.awards).map(([k, a]) => (
        <div key={k} data-testid={`world-award-${k}`}><div className="eyebrow">{a.label}</div>
          {a.picks.length ? a.picks.map((p, i) => (
            <div key={p.unique_id} className="row" style={{ alignItems: "flex-start" }} data-testid={`world-award-${k}-${i}`}>
              <span className={`st ${i === 0 ? "g" : "n"}`} style={{ minWidth: 62, textAlign: "center" }}>{i === 0 ? "Winner" : `${i + 1}${i === 1 ? "nd" : "rd"}`}</span>
              <div style={{ flex: 1 }}><Who r={p} /><small style={{ color: "var(--mut)" }}>avg {p.rating} · {p.goals}G {p.assists}A · {p.minutes} min</small></div>
            </div>)) : <p className="note">Nobody played enough.</p>}
        </div>))}
    </div>
  </div>
);

const LeagueTitle = ({ t, options }) => {
  const act = useAct();
  const [edit, setEdit] = useState(false);
  const [name, setName] = useState(t.league);
  const save = (n) => act(() => api.post("/world/league-names", { orig: t.orig, name: n }), n ? `Renamed to ${n}` : "Back to the automatic name", ["world-report", "world-award-history"]).then((r) => r && setEdit(false));
  if (edit) {
    return (
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 6 }}>
        <input className="inp" style={{ flex: "1 1 160px", height: 30 }} list={`wb-${t.orig}`} maxLength={80} value={name} onChange={(e) => setName(e.target.value)} data-testid={`world-rename-input-${t.orig}`} />
        <datalist id={`wb-${t.orig}`}>{options.map((o) => <option key={o} value={o} />)}</datalist>
        <button className="btn btn-g" disabled={!name.trim()} onClick={() => save(name.trim())} data-testid={`world-rename-save-${t.orig}`}>Save</button>
        {t.named_by_you && <button className="btn" onClick={() => save("")} data-testid={`world-rename-reset-${t.orig}`}>Automatic</button>}
        <button className="btn" onClick={() => setEdit(false)} data-testid={`world-rename-cancel-${t.orig}`}>Cancel</button>
      </div>
    );
  }
  return (
    <div className="eyebrow" style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span data-testid={`world-table-name-${t.orig}`}>{t.league}{t.named_from_workbook ? " *" : ""}{t.named_by_you ? " (your name)" : ""} · {t.country}</span>
      <button className="ib" title={t.orig !== t.league ? `Rename (the save calls it ${t.orig})` : "Rename"} onClick={() => { setName(t.league); setEdit(true); }} data-testid={`world-rename-${t.orig}`}><Pencil size={11} /></button>
    </div>
  );
};

const Tables = ({ d }) => (
  <div className="card" data-testid="world-tables"><div className="ttl"><Table2 size={14} />League tables</div>
    {d.tables_note && <p className="note">{d.tables_note}</p>}
    {d.names_note && <p className="note" data-testid="world-names-note">{d.names_note}</p>}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(300px, 100%), 1fr))", gap: 14, marginTop: 8 }}>
      {d.tables.map((t) => (
        <div key={t.orig} style={{ overflowX: "auto" }} data-testid={`world-table-${t.league}`}><LeagueTitle t={t} options={d.name_options || []} />
          <table className="tbl"><thead><tr><th>#</th><th>Club</th><th>P</th><th>GD</th><th>Pts</th><th></th></tr></thead>
            <tbody>{(d.country || d.league ? t.rows : t.rows.slice(0, 4)).map((r) => <tr key={r.club} style={{ cursor: "default" }}><td className="mono">{r.pos}</td><td>{r.club}</td><td className="mono">{r.p}</td><td className="mono">{r.gd > 0 ? "+" : ""}{r.gd}</td><td className="mono"><b>{r.pts}</b></td>
              <td>{r.move > 0 ? <span className="up"><ArrowUp size={12} />{r.move}</span> : r.move < 0 ? <span className="down"><ArrowDown size={12} />{-r.move}</span> : ""}</td></tr>)}</tbody></table>
        </div>))}
    </div>
  </div>
);

const Transfers = ({ d }) => (
  <div className="card" style={{ overflowX: "auto" }} data-testid="world-transfers"><div className="ttl"><ArrowLeftRight size={14} />The 10 biggest transfers</div>
    {d.transfers.length ? <table className="tbl" style={{ marginTop: 6 }}><thead><tr><th>Player</th><th>From</th><th>To</th><th>Fee</th></tr></thead>
      <tbody>{d.transfers.map((t) => <tr key={t.unique_id} style={{ cursor: "default" }} data-testid={`world-transfer-${t.unique_id}`}><td><b style={{ color: "var(--text)" }}>{t.name}</b> <small>{t.age}</small></td><td>{t.from_club}</td><td>{t.to_club}</td>
        <td className="mono">{t.estimated ? "≈ " : ""}{money(t.fee)}</td></tr>)}</tbody></table>
      : <p className="note">{d.from ? "No moves between clubs this month." : "Transfers appear once FMCC has read two months."}</p>}
  </div>
);

const Leaders = ({ d }) => (
  <div className="card" data-testid="world-leaders"><div className="ttl"><BarChart3 size={14} />Stat leaders<span className="st n">month totals · analytics per 90 this season</span></div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(280px, 100%), 1fr))", gap: 16, marginTop: 8 }}>
      {d.leaders.map((l) => (
        <div key={l.key} data-testid={`world-leader-${l.key}`}><div className="eyebrow">{l.label}</div>
          {l.rows.map((r, i) => <div key={r.unique_id} className="row" style={{ padding: "3px 0" }}><span className="mono" style={{ width: 18 }}>{i + 1}</span><span style={{ flex: 1 }}>{r.name} <small style={{ color: "var(--dim)" }}>{r.club}</small></span><b className="mono">{r.value}</b></div>)}
          {l.u21.length > 0 && <><small className="eyebrow" style={{ display: "block", marginTop: 6 }}>Top 5 under-21</small>
            {l.u21.map((r, i) => <div key={r.unique_id} className="row" style={{ padding: "2px 0" }}><span className="mono" style={{ width: 18 }}>{i + 1}</span><span style={{ flex: 1 }}>{r.name} <small style={{ color: "var(--dim)" }}>{r.age}</small></span><span className="mono">{r.value}</span></div>)}</>}
        </div>))}
    </div>
  </div>
);

const History = ({ d }) => {
  const { data } = useGet("world-award-history", "/world/award-history", { continent: d.continent, country: d.country, league: d.league });
  if (!data) return null;
  const keys = Object.keys(data.labels);
  return (
    <div className="card" style={{ overflowX: "auto" }} data-testid="world-award-history"><div className="ttl"><Trophy size={14} />{d.scope ? `${d.scope}'s` : "World"} award history</div>
      <table className="tbl" style={{ marginTop: 6 }}><thead><tr><th>Month</th>{keys.map((k) => <th key={k}>{data.labels[k].replace(" of the Month", "")}</th>)}</tr></thead>
        <tbody>{data.months.map((m) => <tr key={m.month} style={{ cursor: "default" }} data-testid={`world-history-${m.month}`}>
          <td className="mono">{gameDate(`${m.month}-01`, { month: "short", year: "numeric" })}{m.season_so_far && <small style={{ display: "block", color: "var(--dim)" }}>season so far</small>}</td>
          {keys.map((k) => <td key={k}>{m.winners[k] ? <Who r={m.winners[k]} /> : <span style={{ color: "var(--dim)" }}>—</span>}</td>)}</tr>)}</tbody></table>
    </div>
  );
};

const Scopes = ({ d, open }) => {
  if (d.league) return null;
  const nations = d.countries.filter((c) => !d.continent || c.continent === d.continent);
  const btn = (label, set, id, sub) => <button key={id} className="btn" onClick={() => open(set)} data-testid={id}>{label}{sub && <small style={{ marginLeft: 6, color: "var(--dim)" }}>{sub}</small>}</button>;
  return (
    <div className="card" data-testid="world-countries">
      {!d.continent && !d.country && <><div className="ttl">Continent reports</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>{d.continents.map((c) => btn(c.continent, { continent: c.continent, country: null, league: null }, `world-continent-${c.continent}`, `${c.countries.length} nation${c.countries.length > 1 ? "s" : ""}`))}</div></>}
      {!d.country && <><div className="ttl" style={{ marginTop: d.continent ? 0 : 14 }}>Nation reports</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>{nations.map((c) => btn(c.country, { continent: c.continent, country: c.country, league: null }, `world-country-${c.country}`, `${c.leagues.length} league${c.leagues.length > 1 ? "s" : ""}`))}</div></>}
      {d.country && <><div className="ttl">League reports</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>{(d.countries.find((c) => c.country === d.country)?.leagues || []).map((l) => btn(l, { league: l }, `world-league-${l}`))}</div></>}
    </div>
  );
};

export const WorldReport = ({ d, open }) => (
  <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 16 }} data-testid="world-report">
    <p className="note" data-testid="world-period">{d.season_so_far ? `Season so far, to ${gameDate(d.game_date)}` : `${gameDate(d.from)} to ${gameDate(d.game_date)}`}{d.sample && " · SAMPLE world data in this browser preview"}</p>
    <Scopes d={d} open={open} />
    <News d={d} />
    <Awards d={d} />
    <History d={d} />
    <Tables d={d} />
    <Transfers d={d} />
    <Leaders d={d} />
  </div>
);
