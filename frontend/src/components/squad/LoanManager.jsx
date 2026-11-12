import { useState } from "react";
import { ArrowUp, ArrowDown, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const TONE = { gold: "#F5C542", green: "var(--grn)", red: "var(--red)" };
const gradeColour = (g) => (g.startsWith("A") ? "#F5C542" : g.startsWith("B") ? "var(--grn)" : g.startsWith("C") ? "var(--amb)" : "var(--red)");

const TryLoan = ({ squad }) => {
  const { data: clubs = [] } = useGet("loan-clubs", "/loans/clubs");
  const act = useAct();
  const [uid, setUid] = useState("");
  const [club, setClub] = useState("");
  const [res, setRes] = useState(null);
  const grade = () => act(() => api.post("/loans/try", { unique_id: Number(uid), club }), null, []).then((r) => r && setRes(r));
  return (
    <div className="card" data-testid="loan-try">
      <div className="ttl">Try a loan</div>
      <p className="note" style={{ margin: "4px 0 10px" }}>Pick a loanee and a club to see where he'd fit and how good a move it is.</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <select className="inp" style={{ width: 220 }} value={uid} onChange={(e) => { setUid(e.target.value); setRes(null); }} data-testid="loan-player-select"><option value="">Choose a player</option>
          {squad.map((p) => <option key={p.unique_id} value={p.unique_id}>{p.name} ({p.age})</option>)}</select>
        <select className="inp" style={{ width: 220 }} value={club} onChange={(e) => { setClub(e.target.value); setRes(null); }} data-testid="loan-club-select"><option value="">Choose a club</option>
          {clubs.map((c) => <option key={c}>{c}</option>)}</select>
        <button className="btn btn-p" disabled={!uid || !club} onClick={grade} data-testid="loan-grade-button">Grade this loan</button>
      </div>
      {res && <div style={{ marginTop: 14 }} data-testid="loan-result">
        <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <span className="mono" style={{ fontSize: 34, fontWeight: 700, color: gradeColour(res.grade) }} data-testid="loan-grade">{res.grade}</span>
          <div style={{ flex: 1 }}><b>{res.player.name} to {res.club}</b><small style={{ display: "block", color: "var(--mut)" }} data-testid="loan-reason">{res.reason}.</small>
            <small style={{ display: "block", color: "var(--dim)" }}>League: {res.league || "Not in save yet"} · Facilities: {res.facilities_note}</small></div>
          <button className="btn" onClick={() => act(() => api.post("/loans/track", { unique_id: res.player.unique_id, club: res.club }), "Now tracking this loan", ["loans"])} data-testid="loan-track-button">Track this loan</button>
        </div>
        <div className="ttl" style={{ marginTop: 12, fontSize: 13 }}>{res.club}'s depth chart at his position</div>
        {[...res.depth.slice(0, res.rank - 1), { unique_id: "me", name: `${res.player.name} would slot in here`, age: res.player.age, grade: null, me: true }, ...res.depth.slice(res.rank - 1)].map((p, i) => (
          <div className="row" key={p.unique_id} style={p.me ? { color: "var(--acc)", fontWeight: 700 } : undefined} data-testid={p.me ? "loan-fit-row" : `loan-depth-${p.unique_id}`}>
            <span className="mono">{i + 1}.</span><div style={{ flex: 1 }}>{p.name}<small>{p.age}</small></div><span className="mono">{p.me ? "" : p.grade ?? "—"}</span></div>))}
      </div>}
    </div>
  );
};

const Track = () => {
  const { data } = useGet("loans", "/loans");
  const act = useAct();
  if (!data) return null;
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }} data-testid="loan-track">
      <div className="ttl" style={{ padding: 8 }}>Track loanees</div>
      <table className="tbl pin1"><thead><tr><th>Player</th><th>Club / league</th><th>Minutes</th><th>Rating</th><th>Goals</th><th>Assists</th><th>Facilities</th><th>Trend</th><th></th></tr></thead>
        <tbody>{data.rows.map((r) => (
          <tr key={r.unique_id} style={{ cursor: "default" }} data-testid={`loan-row-${r.unique_id}`}>
            <td><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.age}</small></td><td>{r.club}<small style={{ display: "block", color: "var(--dim)" }}>{r.league || "—"}</small></td>
            <td className="mono">{r.minutes ?? "—"}</td><td className="mono">{r.avg_rating ?? "—"}</td><td className="mono">{r.goals ?? "—"}</td><td className="mono">{r.assists ?? "—"}</td><td><small>Not in save yet</small></td>
            <td title={r.why} data-testid={`loan-trend-${r.unique_id}`} style={{ color: TONE[r.tone] }}>{r.arrow === "up" ? <ArrowUp size={16} /> : <ArrowDown size={16} />}<small style={{ display: "block" }}>{r.why}</small></td>
            <td><button className="ib" aria-label="Stop tracking" onClick={() => act(() => api.delete(`/loans/track/${r.unique_id}`), "Stopped tracking", ["loans"])} data-testid={`loan-untrack-${r.unique_id}`}><X size={13} /></button></td>
          </tr>))}</tbody></table>
      {!data.rows.length && <p className="note" style={{ padding: 10 }} data-testid="loan-track-empty">No loanees tracked yet. Grade a loan above, then press Track this loan.</p>}
      <p className="note" style={{ padding: "4px 10px 10px" }}>{data.note} Gold up arrow: excellent. Green up: going well. Red down: in trouble.</p>
    </div>
  );
};

export const LoanManager = ({ squad }) => (
  <div style={{ display: "grid", gap: 16 }} data-testid="loan-manager"><TryLoan squad={squad} /><Track /></div>
);
