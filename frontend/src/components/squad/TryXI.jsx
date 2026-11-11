import { useEffect, useState } from "react";
import { FlaskConical, X, UserPlus } from "lucide-react";
import { useGet } from "@/lib/ui";
import { openDossier } from "@/components/analysis/StatsTable";

const KEY = "fmcc-try-xi";
export const trialList = () => { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; } };
export const addTrial = (uid) => {
  const l = trialList().filter((x) => x !== uid);
  const full = l.length >= 3;
  localStorage.setItem(KEY, JSON.stringify([...l.slice(full ? 1 : 0), uid]));
  window.dispatchEvent(new Event("fmcc-try-xi"));
  return full;
};

export const TryXI = ({ formation }) => {
  const [ids, setIds] = useState(trialList);
  useEffect(() => { const h = () => setIds(trialList()); window.addEventListener("fmcc-try-xi", h); return () => window.removeEventListener("fmcc-try-xi", h); }, []);
  const { data } = useGet(["try-xi", ids.join(","), formation], "/squad/try-xi", { add: ids.join(","), ...(formation ? { formation } : {}) }, { enabled: ids.length > 0 });
  const remove = (u) => { const l = ids.filter((x) => x !== u); localStorage.setItem(KEY, JSON.stringify(l)); setIds(l); };
  const diff = data ? data.strength_after - data.strength_before : 0;
  useEffect(() => {
    if (data?.skipped?.length) { const l = ids.filter((x) => !data.skipped.includes(x)); localStorage.setItem(KEY, JSON.stringify(l)); setIds(l); }
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="card" style={{ marginTop: 16 }} data-testid="try-xi">
      <div className="ttl"><FlaskConical size={14} />Try in XI<span className="st n">Shadow signings · nothing changes in FM</span></div>
      {!ids.length && <p className="note" data-testid="try-xi-empty">Open any player's dossier (Scout Players → Stats Table, Transfer Market or Club Analysis) and press <b>Try in XI</b> to drop him into your squad here. Up to 3 at once.</p>}
      {ids.length > 0 && data && <>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>{data.trial.map((p) => <span key={p.unique_id} className={`st ${p.in_xi ? "g" : "n"}`} style={{ display: "inline-flex", alignItems: "center", gap: 4, marginLeft: 0, padding: "4px 8px" }} data-testid={`try-xi-chip-${p.unique_id}`}>
          <span style={{ cursor: "pointer" }} onClick={() => openDossier(p.unique_id)}>{p.name} ({p.club}){p.in_xi ? " · starts" : " · doesn't start"}</span>
          <button className="ib" style={{ marginLeft: 4 }} onClick={() => remove(p.unique_id)} aria-label={`Remove ${p.name}`} data-testid={`try-xi-remove-${p.unique_id}`}><X size={11} /></button></span>)}</div>
        <p className="sent" data-testid="try-xi-strength">Best XI strength in {data.label}: <b>{data.strength_before}</b> → <b>{data.strength_after}</b> <span className={`mono ${diff > 0 ? "up" : diff < 0 ? "down" : ""}`}>({diff > 0 ? "+" : ""}{diff})</span>
          {data.dropped.length > 0 && <> · drops out: {data.dropped.join(", ")}</>}</p>
        <div style={{ overflowX: "auto" }}><table className="tbl" data-testid="try-xi-table"><thead><tr><th>Position</th><th>Now</th><th>With trial players</th></tr></thead>
          <tbody>{data.slots.map((s) => <tr key={s.slot} style={{ cursor: "default", background: s.trial ? "rgba(52,211,153,.08)" : undefined }} data-testid={`try-xi-slot-${s.slot}`}>
            <td><b>{s.label}</b></td><td>{s.before || "—"} <span className="mono note">{s.before_rating}</span></td>
            <td>{s.trial && <UserPlus size={12} style={{ display: "inline-block", verticalAlign: "middle", marginRight: 4, color: "#34D399" }} />}{s.after || "—"} <span className="mono note">{s.after_rating}</span></td></tr>)}</tbody></table></div>
      </>}
    </div>
  );
};
