import { useEffect, useState } from "react";
import { Check, X, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg } from "@/lib/api";
import { useAct } from "@/lib/ui";

const val = (v) => (v == null ? <span style={{ color: "var(--dim)" }} title="Real ability values are never shown">Not shown</span> : v);

const Checks = ({ checks }) => (
  <div style={{ marginTop: 4 }} data-testid="batch-checks">
    {checks.map((c) => (
      <div className="row" key={c.key} data-testid={`batch-check-${c.key}`}>
        {c.ok ? <Check size={15} style={{ color: "var(--grn)" }} /> : <X size={15} style={{ color: "var(--red)" }} />}
        <div style={{ flex: 1 }}>{c.label}<small>{c.detail}</small></div>
      </div>
    ))}
  </div>
);

export const BatchDialog = ({ ids, onClose, sources }) => {
  const act = useAct();
  const [p, setP] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!ids) { return; }
    setP(null); setErr(null);
    api.post("/changes/preview", { ids }).then((r) => setP(r.data)).catch((e) => setErr(errMsg(e)));
  }, [ids]);
  const apply = async () => {
    setBusy(true);
    const r = await act(() => api.post("/changes/apply", { preview_id: p.preview_id }), (x) => `Applying ${x.total} change(s). The save was backed up first.`, ["changes", "home", "audit"]);
    setBusy(false);
    if (r) onClose();
  };
  return (
    <Dialog open={!!ids} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl" data-testid="batch-dialog">
        <DialogHeader><DialogTitle>Apply this batch?</DialogTitle>
          <DialogDescription>{p?.live ? "Each change is written into your running FM27 and read back to confirm it took." : "Browser preview: changes go into the sample save. Values are as of the last save read."}</DialogDescription></DialogHeader>
        {err && <p className="note" style={{ color: "var(--red)" }} data-testid="batch-error">{err}</p>}
        {!p && !err && <p className="note"><Loader2 size={14} className="animate-spin" style={{ display: "inline" }} /> Checking the game and reading current values…</p>}
        {p && <>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            <table className="tbl" data-testid="batch-preview-table">
              <thead><tr><th>Player / club</th><th>From</th><th>Field</th><th>Current</th><th>New</th></tr></thead>
              <tbody>{p.rows.map((r) => (
                <tr key={r.id} style={{ cursor: "default" }} data-testid={`batch-preview-row-${r.id}`}>
                  <td>{r.player_name}</td><td>{sources[r.source]}</td><td className="mono">{r.label || { pa: "Potential", ca: "Current ability" }[r.field] || r.field}{r.delta != null && r.entity !== "club" && r.entity !== "shortlist" && ` ${r.delta > 0 ? "+" : ""}${r.delta}`}</td>
                  <td className="mono">{!p.ready ? "—" : r.entity === "shortlist" ? (r.current ? "On shortlist" : "Not on shortlist") : val(r.current)}</td><td className="mono"><b>{!p.ready ? "—" : r.entity === "shortlist" ? "On shortlist" : val(r.new)}</b></td>
                </tr>))}</tbody>
            </table>
          </div>
          <Checks checks={p.checks} />
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 8 }}>
            <p className="note" style={{ flex: 1 }}>{p.ready ? "After applying: press Continue in FM, then save your game to keep the changes." : "Nothing can be applied until every check passes."}</p>
            <button className="btn" onClick={onClose} data-testid="batch-cancel">Cancel</button>
            <button className="btn btn-red" disabled={!p.ready || busy} onClick={apply} data-testid="batch-apply-confirm">Apply batch ({p.rows.length})</button>
          </div>
        </>}
      </DialogContent>
    </Dialog>
  );
};
