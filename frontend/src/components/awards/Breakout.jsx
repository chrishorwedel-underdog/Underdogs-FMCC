import { useState } from "react";
import { Award } from "lucide-react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const Review = ({ c, rules, act }) => {
  const [rule, setRule] = useState(c.review?.category ? rules.find((r) => r.name === c.review.category)?.id : c.rule_id || rules[0]?.id);
  const official = c.review?.status === "official";
  const send = (decision) => act(() => api.post("/breakout/review", { unique_id: c.unique_id, rule_id: rule, decision, note: "" }), decision === "provisional" ? "Provisional award saved" : "Marked as not awarded", ["breakout"]);
  return official ? <span className="st ok">Official · {c.review.category}</span> : (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <select className="inp" style={{ height: 32, width: 200 }} value={rule || ""} onChange={(e) => setRule(e.target.value)} data-testid={`breakout-category-${c.unique_id}`}>{rules.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <button className="btn" onClick={() => send("provisional")} data-testid={`breakout-provisional-${c.unique_id}`}>Award</button>
      <button className="btn" onClick={() => send("rejected")} data-testid={`breakout-reject-${c.unique_id}`}>No</button>
    </div>
  );
};

export const Breakout = () => {
  const { data } = useGet("breakout", "/breakout");
  const act = useAct();
  const [confirm, setConfirm] = useState(false);
  const [nom, setNom] = useState("");
  if (!data) return <p className="note">Loading Breakout…</p>;
  const prov = data.candidates.filter((c) => c.review?.status === "provisional").length;
  return (
    <div>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <span className="note">Season {data.season} · {data.season_over ? "season end: awards can be made official" : "season still running"}</span>
        <input className="inp mono" style={{ width: 160, marginLeft: "auto" }} placeholder="Nominate by game ID" value={nom} onChange={(e) => setNom(e.target.value)} data-testid="breakout-nominate-id" />
        <button className="btn" disabled={!nom} onClick={() => act(() => api.post("/breakout/nominations", { unique_id: Number(nom), note: "" }), "Nominated", ["breakout"]).then(() => setNom(""))} data-testid="breakout-nominate-button">Nominate</button>
        <button className="btn btn-p" disabled={!prov} onClick={() => setConfirm(true)} data-testid="breakout-finalise-button"><Award size={13} />Make {prov} award(s) official</button>
      </div>
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl" data-testid="breakout-table">
          <thead><tr><th>Player</th><th>Age</th><th>Minutes</th><th>Rating</th><th>Growth</th><th>Goals+Assists</th><th>Qualifies for</th><th>Review</th></tr></thead>
          <tbody>{data.candidates.map((c) => (
            <tr key={c.unique_id} style={{ cursor: "default" }} data-testid={`breakout-row-${c.unique_id}`}>
              <td><b style={{ color: "var(--text)" }}>{c.name}</b>{c.nominated && <span className="tag st b">Nominated</span>}{c.review?.status === "provisional" && <span className="tag st a">Provisional</span>}{c.review?.status === "rejected" && <span className="tag st n">Not awarded</span>}
                {c.review && <small style={{ display: "block", color: "var(--dim)" }}>{c.review.revisions} review version(s)</small>}</td>
              <td>{c.age}</td><td className="mono">{c.minutes}</td><td className="mono">{c.avg_rating ?? "—"}</td><td className="mono">{c.ca_growth > 0 ? "+" : ""}{c.ca_growth}</td><td className="mono">{c.goals + c.assists}</td>
              <td>{c.category || <span style={{ color: "var(--dim)" }}>No rule yet</span>}</td><td><Review c={c} rules={data.rules} act={act} /></td>
            </tr>))}</tbody>
        </table>
        {!data.candidates.length && <p className="note" style={{ padding: 10 }}>No candidates yet. Players appear here once they meet a Breakout rule or you nominate them.</p>}
      </div>
      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent data-testid="breakout-finalise-dialog">
          <AlertDialogHeader><AlertDialogTitle>Make {prov} award(s) official?</AlertDialogTitle>
            <AlertDialogDescription>{data.season_over ? "" : "The season isn't over yet. "}Each reward is rolled within its rule's range and added to Game changes. Official awards can't be revised.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => act(() => api.post("/breakout/finalise"), (d) => `${d.official} award(s) made official and queued`, ["breakout", "changes", "home"])} data-testid="breakout-finalise-confirm">Make official</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
