import { useState } from "react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";

export const RoleWeights = ({ open, onClose, roles }) => {
  const { data: saved = {} } = useGet("role-weights", "/analysis/roles");
  const act = useAct();
  const [key, setKey] = useState(roles[0].key);
  const r = roles.find((x) => x.key === key);
  const attrs = [...new Set([...r.with_ball, ...r.without_ball])];
  const w = saved[key] || {};
  const set = (a, v) => act(() => api.put(`/analysis/roles/${key}`, { weights: { ...w, [a]: v } }), null, ["role-weights", "analysis-table"]);
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent data-testid="role-weights-dialog" style={{ maxWidth: 560 }}>
        <DialogHeader><DialogTitle>Role weightings</DialogTitle><DialogDescription>Make an attribute count more (up to 5) or less (0 = ignore) for a role. Role fit everywhere updates straight away.</DialogDescription></DialogHeader>
        <select className="inp" style={{ height: 34 }} value={key} onChange={(e) => setKey(e.target.value)} data-testid="rw-role">{roles.map((x) => <option key={x.key} value={x.key}>{x.name}</option>)}</select>
        <div style={{ display: "grid", gap: 6, maxHeight: "50vh", overflow: "auto" }}>
          {attrs.map((a) => <label key={a} className="note" style={{ display: "grid", gridTemplateColumns: "160px 1fr 30px", gap: 8, alignItems: "center" }}>
            {a.replace(/_/g, " ")}{r.with_ball.includes(a) ? " (ball)" : " (no ball)"}
            <input type="range" min={0} max={5} step={0.5} value={w[a] ?? 1} onChange={(e) => set(a, Number(e.target.value))} data-testid={`rw-${a}`} /><b className="mono">{w[a] ?? 1}</b></label>)}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <button className="btn" onClick={() => act(() => api.delete(`/analysis/roles/${key}`), "Back to standard weightings", ["role-weights", "analysis-table"])} data-testid="rw-reset">Reset this role</button>
          <button className="btn btn-g" onClick={onClose} data-testid="rw-close">Done</button></div>
      </DialogContent>
    </Dialog>
  );
};
