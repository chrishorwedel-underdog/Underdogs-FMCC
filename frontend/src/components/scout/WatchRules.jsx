import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg } from "@/lib/api";

const KINDS = [["value", "Value"], ["grade", "Grade"], ["contract", "Contract ends within"], ["move", "Becomes a free agent or moves club"]];
const fresh = { kind: "value", op: "below", amount: 5 };
const toForm = (r) => ({ kind: r.kind, op: r.op, amount: r.kind === "value" ? r.amount / 1e6 : r.amount });

const RuleRow = ({ r, i, set, del }) => (
  <div className="rule-row" data-testid={`watch-rule-${i}`}>
    <select className="inp" value={r.kind} onChange={(e) => set({ ...r, kind: e.target.value, amount: { value: 5, grade: 60, contract: 6, move: 0 }[e.target.value] })} aria-label="Rule type" data-testid={`watch-rule-kind-${i}`}>
      {KINDS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
    {(r.kind === "value" || r.kind === "grade") && <select className="inp" value={r.op} onChange={(e) => set({ ...r, op: e.target.value })} aria-label="Below or above" data-testid={`watch-rule-op-${i}`}>
      <option value="below">goes below</option><option value="above">goes above</option></select>}
    {r.kind !== "move" && <span className="rule-amt">{r.kind === "value" && "£"}<input className="inp" type="number" min={r.kind === "value" ? 0.1 : 1} step={r.kind === "value" ? 0.5 : 1} value={r.amount}
      onChange={(e) => set({ ...r, amount: e.target.value })} aria-label="Amount" data-testid={`watch-rule-amount-${i}`} />{r.kind === "value" ? "m" : r.kind === "contract" ? " months" : ""}</span>}
    <button className="ib" style={{ width: 30, height: 30 }} onClick={del} aria-label="Remove rule" data-testid={`watch-rule-remove-${i}`}><Trash2 size={13} /></button>
  </div>
);

export const WatchRules = ({ row, onClose }) => {
  const qc = useQueryClient();
  const [rules, setRules] = useState(() => (row.rules || []).map(toForm));
  const [busy, setBusy] = useState(false);
  const save = async (list) => {
    setBusy(true);
    try {
      await api.put(`/watch/${row.unique_id}/rules`, { rules: list.map((r) => ({ kind: r.kind, op: r.op, amount: r.kind === "value" ? Number(r.amount) * 1e6 : Number(r.amount) })) });
      toast.success(list.length ? `Saved ${list.length} rule${list.length > 1 ? "s" : ""} for ${row.last.name}` : `${row.last.name} is back on the standard alerts`);
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      onClose();
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent data-testid="watch-rules-dialog">
        <DialogHeader>
          <DialogTitle>Alert rules for {row.last.name}</DialogTitle>
          <DialogDescription>With your own rules, only they alert you for this player and the standard alerts stop. Each rule alerts once each time it becomes true.</DialogDescription>
        </DialogHeader>
        <div style={{ display: "grid", gap: 8 }}>
          {rules.map((r, i) => <RuleRow key={i} r={r} i={i} set={(n) => setRules(rules.map((x, j) => (j === i ? n : x)))} del={() => setRules(rules.filter((_, j) => j !== i))} />)}
          {!rules.length && <p className="note" data-testid="watch-rules-none">No rules yet, so the standard alerts apply: grade ±2, value ±10% and contract changes.</p>}
          {rules.length < 6 && <button className="btn" style={{ justifySelf: "start" }} onClick={() => setRules([...rules, { ...fresh }])} data-testid="watch-rule-add"><Plus size={13} />Add a rule</button>}
          <small className="note">Now: grade {row.last.grade ?? "—"}, value £{((row.last.value || 0) / 1e6).toFixed(1)}m, {row.last.months_left ?? "—"} months left on his contract.</small>
        </div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 8 }}>
          {!!row.rules?.length && <button className="btn" disabled={busy} onClick={() => save([])} data-testid="watch-rules-reset">Use standard alerts</button>}
          <button className="btn btn-p" disabled={busy} onClick={() => save(rules)} data-testid="watch-rules-save">Save rules</button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
