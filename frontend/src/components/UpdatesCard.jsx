import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { RefreshCw, ArrowUpCircle, Undo2 } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { api, ago, errMsg } from "@/lib/api";

const LABEL = { up_to_date: ["Up to date", "ok"], update_available: ["Update available", "a"], check_failed: ["Couldn't check", "r"], no_source: ["No release page yet", "n"] };

const Comp = ({ c, onApply, onRollback, busy }) => {
  const [text, tone] = LABEL[c.status] || ["Not checked", "n"];
  return (
    <div className="row" data-testid={`update-row-${c.key}`}>
      <div style={{ flex: 1 }}><b>{c.name}</b> <span className="mono" style={{ color: "var(--mut)", fontSize: 12 }}>{c.installed_version}</span><small>{c.role}{c.message ? ` · ${c.message}` : ""}</small></div>
      <span className={`st ${tone}`} data-testid={`update-status-${c.key}`}>{text}{c.status === "update_available" ? ` · ${c.latest_version}` : ""}</span>
      {c.status === "update_available" && <button className="btn btn-p" disabled={busy} onClick={() => onApply(c)} data-testid={`update-apply-${c.key}`}><ArrowUpCircle size={14} />Update now</button>}
      {c.previous_version && <button className="btn" disabled={busy} onClick={() => onRollback(c)} title={`Go back to ${c.previous_version}`} data-testid={`update-rollback-${c.key}`}><Undo2 size={14} /></button>}
    </div>
  );
};

export const UpdatesCard = ({ autoInstall }) => {
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [busy, setBusy] = useState(false);
  const { data } = useQuery({ queryKey: ["updates"], queryFn: () => api.get("/updates").then((r) => r.data) });
  const act = async (fn, ok) => {
    setBusy(true);
    try { await fn(); toast.success(ok); qc.invalidateQueries({ queryKey: ["updates"] }); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  const check = () => act(() => api.post("/updates/check"), "Update check finished");
  const fired = useRef(false);
  useEffect(() => {
    if (params.get("check") && !fired.current) { fired.current = true; setParams({}); check(); }
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps
  const setAuto = (v) => act(() => api.put("/settings/auto-install", { auto_install: v }).then(() => qc.invalidateQueries({ queryKey: ["state"] })), v ? "Updates will install on their own" : "Updates will ask first");
  return (
    <div className="card rise d2" data-testid="updates-card">
      <div className="ttl">Updates<span style={{ marginLeft: "auto" }} /><button className="btn" disabled={busy} onClick={check} data-testid="check-updates-button"><RefreshCw size={14} className={busy ? "animate-spin" : ""} />Check for updates</button></div>
      <p className="note" style={{ marginTop: 6 }} data-testid="updates-last-check">Checked automatically once a week · last check {ago(data?.last_check)}</p>
      <div style={{ marginTop: 6 }}>{data?.components?.map((c) => <Comp key={c.key} c={c} busy={busy}
        onApply={(x) => act(() => api.post(`/updates/${x.key}/apply`), `${x.name} updated to ${x.latest_version}`)}
        onRollback={(x) => act(() => api.post(`/updates/${x.key}/rollback`), `${x.name} went back to ${x.previous_version}`)} />)}</div>
      <div className="row"><div style={{ flex: 1 }}>Install updates on their own<small>Off: FMCC asks before installing</small></div><Switch checked={!!autoInstall} onCheckedChange={setAuto} data-testid="auto-install-switch" /></div>
      <p className="note" style={{ marginTop: 8 }}>Browser preview: versions are checked live on GitHub, but "Update now" only records the change. Files are swapped in the Windows program.</p>
    </div>
  );
};
