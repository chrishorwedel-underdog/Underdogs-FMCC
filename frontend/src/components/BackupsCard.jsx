import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { DatabaseBackup, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { api, ago, errMsg } from "@/lib/api";

export const BackupsCard = () => {
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [busy, setBusy] = useState(false);
  const [restore, setRestore] = useState(null);
  const { data = [] } = useQuery({ queryKey: ["backups"], queryFn: () => api.get("/backups").then((r) => r.data) });
  const backup = async () => {
    setBusy(true);
    try { await api.post("/backups"); toast.success("Backup saved and verified"); qc.invalidateQueries({ queryKey: ["backups"] }); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  const fired = useRef(false);
  useEffect(() => {
    if (params.get("backup") && !fired.current) { fired.current = true; setParams({}); backup(); }
  }, [params]); // eslint-disable-line react-hooks/exhaustive-deps
  const doRestore = async () => {
    setBusy(true);
    try { await api.post(`/backups/${restore.id}/restore`); toast.success("Data restored"); setRestore(null); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div className="card rise d3" data-testid="backups-card">
      <div className="ttl">Data backups<span style={{ marginLeft: "auto" }} /><button className="btn btn-p" disabled={busy} onClick={backup} data-testid="backup-now-button"><DatabaseBackup size={14} />Back up now</button></div>
      <p className="note" style={{ marginTop: 6 }}>A backup is made automatically before each save is read. Each one is checked after it is written.</p>
      <div style={{ marginTop: 6, maxHeight: 320, overflowY: "auto" }}>
        {data.map((b, i) => (
          <div className="row" key={b.id} data-testid={`backup-row-${i}`}>
            <ShieldCheck size={16} style={{ color: b.verified ? "var(--grn)" : "var(--red)" }} />
            <div style={{ flex: 1 }}>{b.reason}<small>{ago(b.created_at)} · {b.counts.snapshots} saves · {b.verified ? "verified" : "not verified"}</small></div>
            <button className="btn" onClick={() => setRestore(b)} data-testid={`backup-restore-${i}`}>Restore</button>
          </div>
        ))}
      </div>
      <AlertDialog open={!!restore} onOpenChange={(o) => !o && setRestore(null)}>
        <AlertDialogContent data-testid="restore-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Restore this backup?</AlertDialogTitle>
            <AlertDialogDescription>FMCC's data goes back to "{restore?.reason}" ({ago(restore?.created_at)}). Your current data is backed up first, so you can undo this. Your FM save files are not touched.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="restore-cancel">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={doRestore} disabled={busy} data-testid="restore-confirm">Restore</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
