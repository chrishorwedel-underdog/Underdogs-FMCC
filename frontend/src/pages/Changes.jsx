import { useState } from "react";
import { Pause, Play, Undo2, Check, X, ShieldCheck } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertTriangle } from "lucide-react";
import { api, ago } from "@/lib/api";
import { useGet, useAct, PageHead } from "@/lib/ui";

const Modes = ({ d, act }) => (
  <div className="card" data-testid="change-modes">
    <div className="ttl">How changes are applied</div>
    {Object.entries(d.sources).map(([k, l]) => (
      <div className="row" key={k}><div style={{ flex: 1 }}>{l}<small>{d.modes[k] === "auto" ? "Apply automatically" : "Ask me first"}</small></div>
        <Switch checked={d.modes[k] === "auto"} onCheckedChange={(v) => act(() => api.put("/changes/modes", { source: k, mode: v ? "auto" : "ask" }), null, ["changes"])} data-testid={`mode-${k}`} /></div>
    ))}
    <div className="row"><div style={{ flex: 1 }}>Show Dynamic Potential details<small>Off: DP values stay hidden everywhere</small></div>
      <Switch checked={d.reveal_dp} onCheckedChange={(v) => act(() => api.put("/changes/reveal", { reveal: v }), null, ["changes", "audit"])} data-testid="reveal-dp-switch" /></div>
  </div>
);

const Queue = ({ d, act }) => {
  const [sel, setSel] = useState([]);
  const ids = d.queued.map((q) => q.id);
  const chosen = sel.filter((s) => ids.includes(s));
  const all = chosen.length === ids.length && ids.length > 0;
  return (
    <div className="card" style={{ padding: 8 }} data-testid="change-queue">
      <div className="ttl" style={{ padding: 10 }}>Waiting for you<span className="st a mono">{d.queued.length}</span><span style={{ marginLeft: "auto" }} />
        <button className="btn" disabled={!chosen.length} onClick={() => act(() => api.post("/changes/reject", { ids: chosen }), "Changes rejected", ["changes", "home"])} data-testid="queue-reject-button"><X size={13} />Reject</button>
        <button className="btn btn-p" disabled={!chosen.length || !d.editor_ok} onClick={() => act(() => api.post("/changes/apply", { ids: chosen }), (r) => `Applying ${r.total} change(s). A backup was saved first.`, ["changes", "home", "audit"])} data-testid="queue-apply-button"><Check size={13} />Apply {chosen.length || ""}</button></div>
      <table className="tbl">
        <thead><tr><th><Checkbox checked={all} onCheckedChange={(v) => setSel(v ? ids : [])} data-testid="queue-select-all" /></th><th>Player</th><th>From</th><th>Exact change</th><th>Queued</th></tr></thead>
        <tbody>{d.queued.map((q) => (
          <tr key={q.id} style={{ cursor: "default" }} data-testid={`queue-row-${q.id}`}>
            <td><Checkbox checked={chosen.includes(q.id)} onCheckedChange={(v) => setSel(v ? [...chosen, q.id] : chosen.filter((x) => x !== q.id))} /></td>
            <td>{q.player_name}{q.club && <small style={{ display: "block", color: "var(--dim)" }}>{q.club}</small>}</td><td>{d.sources[q.source]}</td>
            <td className="mono" data-testid={`queue-delta-${q.id}`}>{q.delta == null ? <span style={{ color: "var(--dim)" }}>Hidden</span> : `${q.field.toUpperCase()} ${q.delta > 0 ? "+" : ""}${q.delta}`}</td><td><small>{ago(q.created_at)}</small></td>
          </tr>))}</tbody>
      </table>
      {!d.queued.length && <p className="note" style={{ padding: 10 }}>Nothing waiting.</p>}
    </div>
  );
};

const Batches = ({ d, act }) => (
  <div className="card" data-testid="batches">
    <div className="ttl">Batches</div>
    {d.batches.length === 0 && <p className="note" style={{ marginTop: 8 }}>No batches yet.</p>}
    {d.batches.map((b, i) => (
      <div className="row" key={b.id} data-testid={`batch-row-${i}`}>
        <div style={{ flex: 1 }}>
          <div className="mb" style={{ gridTemplateColumns: "1fr 60px" }}><div className="track"><i style={{ width: `${(b.done / b.total) * 100}%`, background: b.status === "undone" ? "var(--mut)" : "var(--acc)" }} /></div><span className="mono">{b.done}/{b.total}</span></div>
          <small><ShieldCheck size={11} style={{ display: "inline", color: "var(--grn)" }} /> backup saved · {ago(b.created_at)}{b.error ? ` · ${b.error}` : ""}</small>
        </div>
        <span className={`st ${b.status === "done" ? "ok" : b.status === "running" ? "g" : b.status === "paused" ? "a" : "n"}`} data-testid={`batch-status-${i}`}>{b.status}</span>
        {b.status === "running" && <button className="btn" onClick={() => act(() => api.post(`/changes/batches/${b.id}/pause`), "Paused", ["changes"])} data-testid={`batch-pause-${i}`}><Pause size={13} /></button>}
        {b.status === "paused" && <button className="btn" onClick={() => act(() => api.post(`/changes/batches/${b.id}/resume`), "Resumed", ["changes"])} data-testid={`batch-resume-${i}`}><Play size={13} /></button>}
        {["done", "paused"].includes(b.status) && <button className="btn" onClick={() => act(() => api.post(`/changes/batches/${b.id}/undo`), (r) => `${r.undone} change(s) undone`, ["changes", "audit", "home"])} data-testid={`batch-undo-${i}`}><Undo2 size={13} />Undo</button>}
      </div>
    ))}
  </div>
);

const Audit = () => {
  const { data = [] } = useGet("audit", "/audit", undefined, { refetchInterval: 3000 });
  return (
    <div className="card" data-testid="audit-trail"><div className="ttl">Audit trail</div>
      <div style={{ maxHeight: 420, overflowY: "auto" }}>
        {data.map((a) => <div className="row" key={a.id}><div style={{ flex: 1 }}><b style={{ textTransform: "capitalize" }}>{a.action}</b>{a.player_name ? ` · ${a.player_name}` : ""}<small>{a.detail} · {a.source}</small></div><small>{ago(a.at)}</small></div>)}
      </div>
    </div>
  );
};

export default function Changes() {
  const act = useAct();
  const { data: d } = useGet("changes", "/changes", undefined, { refetchInterval: (q) => (q.state.data?.batches?.some((b) => b.status === "running") ? 800 : 5000) });
  if (!d) return <p className="note">Loading game changes…</p>;
  return (
    <div data-testid="changes-page">
      <PageHead eyebrow={`Game editor · ${d.edition} · ${d.editor_ok ? "supported" : "not supported"}`} title="Game changes" />
      <div className="banner" style={{ marginBottom: 20 }} data-testid="editor-sample-banner"><AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>Browser preview: changes are written to the sample save, not to Football Manager. They show up the next time a save is read, just as real changes stick when FM next saves.</span></div>
      <div className="homegrid">
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Queue d={d} act={act} /><Audit /></div>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Modes d={d} act={act} /><Batches d={d} act={act} /></div>
      </div>
    </div>
  );
}
