import { useState } from "react";
import { Check, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { RecordCard } from "./Overview";
import { PlayerDetail } from "./PlayerDetail";

export const NeedsReview = () => {
  const { data = [] } = useGet("dp-records", "/dp/records");
  const act = useAct();
  const [open, setOpen] = useState(null);
  const rows = data.filter((r) => ["needs_review", "held", "flag"].includes(r.status));
  const decide = (r, approve) => act(() => api.post(`/dp/records/${r.id}/decide`, { approve }), approve ? `${r.name}: approved and sent to your save` : `${r.name}: rejected`, ["dp-records", "dp-overview", "changes"]);
  return (
    <div style={{ display: "grid", gap: 12 }} data-testid="dp-needs-review">
      <p className="note">Ratings-only growth above +4, assessments with too few comparison players, and declines held for missing evidence wait here.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: 12 }}>
        {rows.map((r) => (
          <RecordCard key={r.id} r={r} open={setOpen}>
            <div style={{ display: "flex", gap: 8, marginTop: 10 }} onClick={(e) => e.stopPropagation()}>
              <button className="btn btn-g" disabled={!r.change} onClick={() => decide(r, true)} data-testid={`dp-approve-${r.kind}-${r.unique_id}`}><Check size={13} />Approve</button>
              <button className="btn" onClick={() => decide(r, false)} data-testid={`dp-reject-${r.kind}-${r.unique_id}`}><X size={13} />Reject</button>
            </div>
          </RecordCard>))}
      </div>
      {!rows.length && <p className="note" data-testid="dp-review-empty">Nothing needs your review.</p>}
      <PlayerDetail uid={open} onClose={() => setOpen(null)} />
    </div>
  );
};
