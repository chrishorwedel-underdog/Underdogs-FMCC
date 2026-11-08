import { useState } from "react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { useScout, fmtMoney, usePost, ContractTag } from "./ctx";

export const MyClubTab = () => {
  const { view, prefs, openPlayer } = useScout();
  const [g, setG] = useState(null);
  const { data = [] } = useGet("myclub", "/scout/myclub", { view });
  const { data: imp } = useGet("myclub-improvers", `/scout/myclub/${g}`, { view }, { enabled: !!g });
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(260px,340px) 1fr", gap: 16 }}>
      <div className="card" data-testid="myclub-positions"><div className="ttl">Your squad by position<span className="st n">weakest first</span></div>
        {data.map((r) => <div key={r.group} className="row" style={{ cursor: "pointer", background: g === r.group ? "rgba(76,141,255,.06)" : undefined }} onClick={() => setG(r.group)} data-testid={`myclub-pos-${r.group}`}>
          <div style={{ flex: 1 }}>{r.label}<small>{r.best ? `${r.best.name} · ${r.players} players` : "Nobody graded yet"}</small></div><span className="mono" style={{ color: "var(--acc)" }}>{r.rating || "—"}</span></div>)}
      </div>
      <div className="card" style={{ overflowX: "auto" }} data-testid="myclub-improvers">
        {!g ? <div className="soon">Click a position to see the players who would improve it, with their cost.</div> : <>
          <div className="ttl">Would improve {data.find((d) => d.group === g)?.label}<span className="st n">your best: {imp?.bar ?? "—"}</span></div>
          <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>Player</th><th>Age</th><th>Grade</th><th>Gain</th><th>Value</th><th>Fair price</th></tr></thead>
            <tbody>{imp?.rows.map((r) => <tr key={r.unique_id} onClick={() => openPlayer(r.unique_id)} data-testid={`improver-${r.unique_id}`}><td><b>{r.name}</b><ContractTag m={r.months_left} /><small style={{ display: "block", color: "var(--dim)" }}>{r.club}</small></td>
              <td>{r.age}</td><td className="mono">{r.grade_global}</td><td className="mono" style={{ color: "var(--grn)" }}>+{r.gain}</td><td className="mono">{fmtMoney(r.value, prefs)}</td><td className="mono">{r.fair_price ? fmtMoney(r.fair_price, prefs) : "—"}</td></tr>)}</tbody></table>
          {imp && !imp.rows.length && <p className="note" style={{ marginTop: 8 }}>Nobody in the save beats your current best here.</p>}</>}
      </div>
    </div>
  );
};

const Offers = () => {
  const { prefs } = useScout();
  const [q, setQ] = useState("");
  const [pick, setPick] = useState(null);
  const [amount, setAmount] = useState("");
  const [dir, setDir] = useState("buy");
  const [res, setRes] = useState(null);
  const { data } = usePost("offer-search", "/scout/players", { q, limit: 6, view: "moneyball" }, { enabled: q.length > 1 && !pick });
  const act = useAct();
  const check = async () => setRes(await act(() => api.post("/scout/offer", { unique_id: pick.unique_id, amount: Math.round(Number(amount) * 1e6), direction: dir }), null, ["audit"]));
  return (
    <div className="card" data-testid="offers-card"><div className="ttl">Offers</div>
      <p className="note" style={{ marginTop: 4 }}>Check a bid against his fair price before you send or accept it. Amounts in millions of pounds.</p>
      {pick ? <div className="row"><b style={{ flex: 1 }}>{pick.name}<small>{pick.club} · value {fmtMoney(pick.value, prefs)}</small></b><button className="btn" onClick={() => { setPick(null); setRes(null); }} data-testid="offer-change-player">Change</button></div>
        : <><input className="inp" style={{ marginTop: 8 }} placeholder="Find a player" value={q} onChange={(e) => setQ(e.target.value)} data-testid="offer-search" />
          {data?.rows.map((r) => <div key={r.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => setPick(r)} data-testid={`offer-pick-${r.unique_id}`}>{r.name}<small style={{ marginLeft: 8 }}>{r.club}</small></div>)}</>}
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <div className="seg">{[["buy", "We're buying"], ["sell", "We're selling"]].map(([k, l]) => <button key={k} className={dir === k ? "on" : ""} onClick={() => setDir(k)} data-testid={`offer-dir-${k}`}>{l}</button>)}</div>
        <input className="inp" style={{ width: 120 }} type="number" placeholder="£m" value={amount} onChange={(e) => setAmount(e.target.value)} data-testid="offer-amount" />
        <button className="btn btn-p" disabled={!pick || !amount} onClick={check} data-testid="offer-check">Check</button>
      </div>
      {res && <div className="soon" data-testid="offer-verdict"><b>{res.verdict}</b>{res.fair_price ? ` · fair price ${fmtMoney(res.fair_price, prefs)} · bid is ${res.ratio}× fair · confidence ${res.confidence}` : ` · ${res.detail}`}</div>}
    </div>
  );
};

export const DealsTab = () => {
  const { view, prefs, openPlayer } = useScout();
  const { data = [] } = useGet("deals", "/scout/deals", { view });
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr minmax(300px,380px)", gap: 16 }}>
      <div className="card" style={{ overflowX: "auto" }} data-testid="deal-finder"><div className="ttl">Deal Finder<span className="st n">selling well under fair price</span></div>
        <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>Player</th><th>Age</th><th>Grade</th><th>Value</th><th>Fair price</th><th>Under by</th><th>Confidence</th></tr></thead>
          <tbody>{data.map((r) => <tr key={r.unique_id} onClick={() => openPlayer(r.unique_id)} data-testid={`deal-${r.unique_id}`}><td><b>{r.name}</b><ContractTag m={r.months_left} /><small style={{ display: "block", color: "var(--dim)" }}>{r.club} · {r.cohort}</small></td>
            <td>{r.age}</td><td className="mono">{r.grade_global}</td><td className="mono">{fmtMoney(r.value, prefs)}</td><td className="mono">{fmtMoney(r.fair_price, prefs)}</td><td className="mono" style={{ color: "var(--grn)" }}>{r.discount}%</td><td>{r.confidence}</td></tr>)}</tbody></table>
        {!data.length && <p className="note">No bargains right now.</p>}
      </div>
      <Offers />
    </div>
  );
};
