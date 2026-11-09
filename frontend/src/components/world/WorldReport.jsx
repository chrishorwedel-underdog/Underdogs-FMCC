import { Newspaper, Trophy, ArrowLeftRight, BarChart3, Table2, ArrowUp, ArrowDown } from "lucide-react";
import { gameDate } from "@/lib/api";

const money = (v) => (v >= 1e6 ? `€${(v / 1e6).toFixed(1)}m` : `€${Math.round(v / 1000)}k`);
const Who = ({ r }) => <><b style={{ color: "var(--text)" }}>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.age} · {r.club}</small></>;

const News = ({ d }) => (
  <div className="card" data-testid="world-news"><div className="ttl"><Newspaper size={14} />{d.country ? `${d.country}: top stories` : "The 12 biggest stories"}</div>
    {d.news.length ? <ol style={{ margin: "8px 0 0", paddingLeft: 20, display: "grid", gap: 6 }}>{d.news.map((n, i) => (
      <li key={i} data-testid={`world-news-${i}`}><span className="st n" style={{ marginRight: 6 }}>{n.tag}</span>{n.text}{!d.country && <small style={{ color: "var(--dim)" }}> · {n.country}</small>}</li>))}</ol>
      : <p className="note">No big stories this month.</p>}
  </div>
);

const Awards = ({ d }) => (
  <div className="card" data-testid="world-awards"><div className="ttl"><Trophy size={14} />{d.country ? `${d.country}'s` : "World"} players of the month</div>
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

const Tables = ({ d }) => (
  <div className="card" data-testid="world-tables"><div className="ttl"><Table2 size={14} />League tables</div>
    {d.tables_note && <p className="note">{d.tables_note}</p>}
    {d.names_note && <p className="note" data-testid="world-names-note">{d.names_note}</p>}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(300px, 100%), 1fr))", gap: 14, marginTop: 8 }}>
      {d.tables.map((t) => (
        <div key={t.league} style={{ overflowX: "auto" }} data-testid={`world-table-${t.league}`}><div className="eyebrow">{t.league}{t.named_from_workbook ? " *" : ""} · {t.country}</div>
          <table className="tbl"><thead><tr><th>#</th><th>Club</th><th>P</th><th>GD</th><th>Pts</th><th></th></tr></thead>
            <tbody>{(d.country ? t.rows : t.rows.slice(0, 4)).map((r) => <tr key={r.club} style={{ cursor: "default" }}><td className="mono">{r.pos}</td><td>{r.club}</td><td className="mono">{r.p}</td><td className="mono">{r.gd > 0 ? "+" : ""}{r.gd}</td><td className="mono"><b>{r.pts}</b></td>
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

export const WorldReport = ({ d, openCountry }) => (
  <div style={{ display: "grid", gap: 16 }} data-testid="world-report">
    <p className="note" data-testid="world-period">{d.season_so_far ? `Season so far, to ${gameDate(d.game_date)}` : `${gameDate(d.from)} to ${gameDate(d.game_date)}`}{d.sample && " · SAMPLE world data in this browser preview"}</p>
    {!d.country && <div className="card" data-testid="world-countries"><div className="ttl">Country reports</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>{d.countries.map((c) => <button key={c.country} className="btn" title={c.leagues.join(", ")} onClick={() => openCountry(c.country)} data-testid={`world-country-${c.country}`}>{c.country}<small style={{ marginLeft: 6, color: "var(--dim)" }}>{c.leagues.length} league{c.leagues.length > 1 ? "s" : ""}</small></button>)}</div></div>}
    <News d={d} />
    <Awards d={d} />
    <Tables d={d} />
    <Transfers d={d} />
    <Leaders d={d} />
  </div>
);
