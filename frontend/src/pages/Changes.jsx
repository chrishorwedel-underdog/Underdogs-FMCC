import { useState } from "react";
import { Link } from "react-router-dom";
import { Pause, Play, Undo2, Check, X, ShieldCheck, ChevronDown } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertTriangle } from "lucide-react";
import { api, ago } from "@/lib/api";
import { useGet, useAct, PageHead } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { AuditCard } from "@/components/AuditCard";
import { BatchDialog } from "@/components/BatchDialog";

const Modes = ({ d }) => (
  <div className="card" data-testid="change-modes">
    <div className="ttl">How changes are applied</div>
    <p className="note" style={{ marginTop: 6 }} data-testid="change-mode-text">{d.review_changes
      ? "Review changes before applying is on: changes wait here until you apply them."
      : "Automatic: changes go into your save straight away and a notification lists them. Anything the game can't take yet waits here."}</p>
    <Link to="/features" className="btn" style={{ marginTop: 10, width: "fit-content" }} data-testid="change-mode-features-link">Change this in Features</Link>
  </div>
);

const WORD = { pa: "Potential", ca: "Current ability" };
const what = (q) => (q.entity === "shortlist" ? "Add to FM shortlist" : q.entity === "club" ? `${q.label} → ${q.target}` : `${WORD[q.field] || q.field} ${q.delta > 0 ? "+" : ""}${q.delta}`);

const Queue = ({ d, act }) => {
  const [sel, setSel] = useState([]);
  const [batch, setBatch] = useState(null);
  const ids = d.queued.map((q) => q.id);
  const chosen = sel.filter((s) => ids.includes(s));
  const all = chosen.length === ids.length && ids.length > 0;
  const target = chosen.length ? chosen : ids;
  return (
    <div className="card" style={{ padding: 8 }} data-testid="change-queue">
      <div className="ttl" style={{ padding: 10 }}>Waiting for you<span className="st a mono">{d.queued.length}</span><span style={{ marginLeft: "auto" }} />
        <button className="btn" disabled={!chosen.length} onClick={() => act(() => api.post("/changes/reject", { ids: chosen }), "Changes rejected", ["changes", "home"])} data-testid="queue-reject-button"><X size={13} />Reject</button>
        <button className="btn btn-red" disabled={!target.length || !d.editor_ok} onClick={() => setBatch(target.slice(0, 500))} data-testid="queue-apply-button"><Check size={13} />Apply batch ({Math.min(500, target.length)})</button></div>
      <BatchDialog ids={batch} onClose={() => setBatch(null)} sources={d.sources} />
      <table className="tbl">
        <thead><tr><th><Checkbox checked={all} onCheckedChange={(v) => setSel(v ? ids : [])} data-testid="queue-select-all" /></th><th>Player</th><th>From</th><th>Exact change</th><th>Queued</th></tr></thead>
        <tbody>{d.queued.map((q) => (
          <tr key={q.id} style={{ cursor: "default" }} data-testid={`queue-row-${q.id}`}>
            <td><Checkbox checked={chosen.includes(q.id)} onCheckedChange={(v) => setSel(v ? [...chosen, q.id] : chosen.filter((x) => x !== q.id))} /></td>
            <td>{q.player_name}{q.club && <small style={{ display: "block", color: "var(--dim)" }}>{q.club}</small>}</td><td>{d.sources[q.source]}</td>
            <td className="mono" data-testid={`queue-delta-${q.id}`}>{what(q)}</td><td><small>{ago(q.created_at)}</small></td>
          </tr>))}</tbody>
      </table>
      {!d.queued.length && <p className="note" style={{ padding: 10 }}>Nothing waiting.</p>}
      {d.queued.length > 0 && <p className="note" style={{ padding: "0 10px 10px" }}>Tick changes to apply only those; otherwise the batch holds everything waiting.</p>}
    </div>
  );
};

const TONE = { done: "ok", running: "g", paused: "a", stopped: "r", "partly undone": "a" };

const BatchDetail = ({ id }) => {
  const { data } = useGet("batch", `/changes/batches/${id}`, { id });
  if (!data) return null;
  return (
    <div style={{ padding: "6px 0 10px 4px" }} data-testid={`batch-detail-${id}`}>
      <small style={{ display: "block", marginBottom: 6 }}>Approved by {data.approved_by || "Manager"} · {data.save_backup ? `save copied to ${data.save_backup.file}` : "FMCC backup saved"}</small>
      {data.changes.map((c) => <div key={c.id} style={{ padding: "6px 8px 6px 0", borderTop: "1px solid var(--line)", fontSize: 12.5 }} data-testid={`batch-change-${c.id}`}>
        <b style={{ display: "block" }}>{c.player_name}</b>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 2 }}><span className="mono">{c.entity === "club" && c.old_value != null ? `${c.label} ${c.old_value} → ${c.new_value ?? "—"}` : what(c)}</span>
          <span className={`st ${c.status === "applied" ? "ok" : c.status === "failed" ? "r" : "n"}`} style={{ marginLeft: "auto" }} title={c.error || ""}>{c.status}</span></div></div>)}
    </div>
  );
};

const Batches = ({ d, act }) => {
  const [open, setOpen] = useState(null);
  return (
  <div className="card" data-testid="batches">
    <div className="ttl">Batches</div>
    {d.batches.length === 0 && <p className="note" style={{ marginTop: 8 }}>No batches yet.</p>}
    {d.batches.map((b, i) => (
      <div key={b.id}><div className="row" data-testid={`batch-row-${i}`} style={{ flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 160 }}>
          <div className="mb" style={{ gridTemplateColumns: "1fr 60px" }}><div className="track"><i style={{ width: `${(b.done / b.total) * 100}%`, background: b.status === "undone" ? "var(--mut)" : "var(--acc)" }} /></div><span className="mono">{b.done}/{b.total}</span></div>
          <small><ShieldCheck size={11} style={{ display: "inline", color: "var(--grn)" }} /> backup saved · {ago(b.created_at)}{b.error ? ` · ${b.error}` : ""}</small>
        </div>
        <span className={`st ${TONE[b.status] || "n"}`} data-testid={`batch-status-${i}`}>{b.status}</span>
        <button className="btn" onClick={() => setOpen(open === b.id ? null : b.id)} title="Show each change" data-testid={`batch-open-${i}`}><ChevronDown size={13} /></button>
        {b.status === "running" && <button className="btn" onClick={() => act(() => api.post(`/changes/batches/${b.id}/pause`), "Paused", ["changes"])} data-testid={`batch-pause-${i}`}><Pause size={13} /></button>}
        {b.status === "paused" && <button className="btn" onClick={() => act(() => api.post(`/changes/batches/${b.id}/resume`), "Resumed", ["changes"])} data-testid={`batch-resume-${i}`}><Play size={13} /></button>}
        {["done", "paused", "stopped", "partly undone"].includes(b.status) && b.done > 0 && <button className="btn" onClick={() => window.confirm(`Put back the old values of this batch's applied changes?${d.live ? " FM27 must be running with the same save loaded." : ""}`) && act(() => api.post(`/changes/batches/${b.id}/undo`), (r) => r.error || `${r.undone} change(s) undone`, ["changes", "audit", "home", "batch"])} data-testid={`batch-undo-${i}`}><Undo2 size={13} />Undo batch</button>}
      </div>
      {open === b.id && <BatchDetail id={b.id} />}
      </div>
    ))}
  </div>
  );
};

export default function Changes() {
  const act = useAct();
  const { data: d } = useGet("changes", "/changes", undefined, { refetchInterval: (q) => (q.state.data?.batches?.some((b) => b.status === "running") ? 800 : 5000) });
  if (!d) return <Loading id="changes-loading" label="Loading game changes" />;
  const last = d.batches[0];
  return (
    <div data-testid="changes-page">
      <PageHead eyebrow={`Game editor · ${d.edition} · ${d.live ? (d.editor_ok ? "live FMLibreEditor" : "read-only") : "sample editor"}`} title="Game changes" />
      {!d.live && <div className="banner" style={{ marginBottom: 20 }} data-testid="editor-sample-banner"><AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>Browser preview: changes are written to the sample save, not to Football Manager. They show up the next time a save is read, just as real changes stick when FM next saves.</span></div>}
      {d.live && !d.editor_ok && <div className="banner" style={{ marginBottom: 20 }} data-testid="editor-readonly-banner"><AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} /><span>FM26 saves stay read-only, because FMLibreEditor only supports FM27. Changes stay in the queue and in FMCC's record.</span></div>}
      {last?.status === "done" && last.done > 0 && <div className="banner" style={{ marginBottom: 20, borderColor: "var(--red)" }} data-testid="save-reminder"><AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <span><b>Keep the changes:</b> press Continue in FM, then save your game. FMCC reads that save and shows the new values.</span></div>}
      <div className="homegrid">
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Queue d={d} act={act} /><AuditCard /></div>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Modes d={d} /><Batches d={d} act={act} /></div>
      </div>
    </div>
  );
}
