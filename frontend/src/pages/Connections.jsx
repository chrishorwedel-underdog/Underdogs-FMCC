import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Download, Trash2, RefreshCw, ExternalLink, ShieldAlert, Plug } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { api, ago, errMsg } from "@/lib/api";
import { useGet, PageHead } from "@/lib/ui";

const Status = ({ ok, label, id }) => <span className={`st ${ok ? "ok" : "a"}`} data-testid={`conn-status-${id}`}>{ok ? "Installed" : "Not installed"}{label ? ` · ${label}` : ""}</span>;
const WORK = { ok: ["ok", "Working"], waiting: ["a", "Waiting for FM"], fail: ["r", "Not working"] };

const Row = ({ title, sub, children, id }) => (
  <div className="row" data-testid={`conn-row-${id}`}><div style={{ flex: 1 }}><b>{title}</b><small>{sub}</small></div>{children}</div>
);

export default function Connections() {
  const qc = useQueryClient();
  const { data: d } = useGet("connections", "/connections", undefined, { refetchInterval: 5000 });
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(null);
  const [admin, setAdmin] = useState(false);
  const run = async (url, ok) => {
    setBusy(true);
    try { const { data } = await api.post(url); if (ok) toast.success(typeof ok === "function" ? ok(data) : ok); qc.invalidateQueries({ queryKey: ["connections"] }); qc.invalidateQueries({ queryKey: ["matches"] }); }
    catch (e) { if (e?.response?.status === 403) setAdmin(true); toast.error(errMsg(e)); }
    finally { setBusy(false); setConfirm(null); }
  };
  if (!d) return <p className="note">Checking connections…</p>;
  const ml = d.matchlens || {};
  const w = WORK[ml.working] || ["n", "Not checked"];
  return (
    <div data-testid="connections-page">
      <PageHead eyebrow={`Steam · ${d.edition}`} title="Connections" />
      {!d.desktop && <div className="banner" style={{ marginBottom: 20 }} data-testid="connections-preview-banner"><ShieldAlert size={16} style={{ flexShrink: 0, marginTop: 2 }} /><span>Browser preview: installing is simulated here. The Windows program downloads BepInEx 6 and FMMatchLens from their official release pages and copies them into your Steam FM folder.</span></div>}
      {(admin && d.desktop && !d.is_admin) && <div className="banner" style={{ marginBottom: 20 }} data-testid="admin-banner"><ShieldAlert size={16} /><span style={{ flex: 1 }}>Windows blocked access to the game. FMCC can restart itself as administrator.</span>
        <button className="btn btn-p" onClick={() => run("/connections/restart-admin", "Restarting FMCC as administrator…")} data-testid="restart-admin-button">Restart as administrator</button></div>}
      <div className="homegrid">
        <div className="card" data-testid="matchlens-card">
          <div className="ttl"><Plug size={15} />Match add-on (FMMatchLens)<span style={{ marginLeft: "auto" }} className={`st ${w[0]}`} data-testid="matchlens-working">{w[1]}</span></div>
          <p className="note" style={{ marginTop: 6 }} data-testid="game-folder">{d.game_root ? <>FM folder: <span className="mono">{d.game_root}</span></> : `FMCC couldn't find ${d.edition} in your Steam library.`}{d.game_running ? " · FM is running" : ""}</p>
          <Row id="bepinex" title="BepInEx 6" sub="The add-on loader (IL2CPP x64, the version FMMatchLens needs)"><Status ok={d.bepinex} label={ml.bepinex} id="bepinex" /></Row>
          <Row id="plugin" title="FMMatchLens plugin" sub={`Version ${d.target_version} for ${d.edition}`}><Status ok={d.plugin} label={ml.fmmatchlens} id="plugin" /></Row>
          <Row id="dashboard" title="FMMatchLens dashboard" sub="Live matches and saved .fmlens matches"><Status ok={d.dashboard} id="dashboard" /></Row>
          {ml.message && <p className="note" style={{ marginTop: 10 }} data-testid="matchlens-message">{ml.message}{ml.checked_at ? ` · checked ${ago(ml.checked_at)}` : ""}</p>}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
            {!ml.installed
              ? <button className="btn btn-p" disabled={busy || d.game_running || (d.desktop && !d.game_root)} onClick={() => setConfirm("install")} data-testid="matchlens-install"><Download size={13} />Install match add-on</button>
              : <>
                <button className="btn" disabled={busy} onClick={() => run("/connections/matchlens/check", (r) => r.message)} data-testid="matchlens-check"><RefreshCw size={13} />Check it's working</button>
                <button className="btn" disabled={busy} onClick={() => run("/connections/matchlens/dashboard", "Opening the dashboard")} data-testid="matchlens-dashboard"><ExternalLink size={13} />Open match dashboard</button>
                <button className="btn btn-d" disabled={busy || d.game_running} onClick={() => setConfirm("remove")} data-testid="matchlens-remove"><Trash2 size={13} />Remove match add-on</button></>}
          </div>
          {d.game_running && <p className="note" style={{ marginTop: 8, color: "var(--amb)" }} data-testid="fm-running-note">Close FM to install or remove the add-on.</p>}
          {ml.installed && <p className="note" style={{ marginTop: 8 }}>FMCC's Matches page keeps showing sample data. Reading .fmlens files there waits until their format is known.</p>}
        </div>
        <div className="card" data-testid="editor-card">
          <div className="ttl">Live game changes (FMLibreEditor)<span style={{ marginLeft: "auto" }} className={`st ${d.editor_supported ? "ok" : "a"}`} data-testid="editor-status">{d.editor_supported ? "FM27: supported" : "FM26: read-only"}</span></div>
          <p className="note" style={{ marginTop: 6 }}>{d.editor_supported
            ? "Approved changes are written into your running FM27 by FMLibreEditor's command-line tool, built into FMCC. Each batch is checked against your game version and save before anything is written."
            : "FMLibreEditor only supports FM27, so FM26 saves stay read-only. Changes stay in the queue and in FMCC's record."}</p>
          {d.desktop && <Row id="probe" title="Command-line tool" sub="fmlibre-probe, GPL-3.0"><span className={`st ${d.probe_present ? "ok" : "r"}`}>{d.probe_present ? "Built in" : "Missing"}</span></Row>}
          {d.desktop && <Row id="admin" title="Running as administrator" sub="Only needed if Windows blocks access to the game"><span className="st n">{d.is_admin ? "Yes" : "No"}</span></Row>}
        </div>
      </div>
      <AlertDialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent data-testid="matchlens-confirm-dialog">
          <AlertDialogHeader><AlertDialogTitle>{confirm === "install" ? "Install the match add-on?" : "Remove the match add-on?"}</AlertDialogTitle>
            <AlertDialogDescription>{confirm === "install"
              ? `FMCC downloads BepInEx 6 (IL2CPP x64), FMMatchLens ${d.target_version} and its dashboard from their official release pages and adds them to your FM folder. It never overwrites a file that's already there, and records every file it adds. FM must stay closed.`
              : `FMCC removes exactly the ${ml.files?.length || 0} file(s) it added, and nothing else. Files BepInEx made itself, and your match archives, stay.`}</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction disabled={busy} onClick={(e) => { e.preventDefault(); confirm === "install" ? run("/connections/matchlens/install", "Installed. Start FM once until the main menu, then press Check it's working.") : run("/connections/matchlens/remove", (r) => `Removed ${r.removed} file(s)`); }} data-testid="matchlens-confirm">{confirm === "install" ? "Install" : "Remove"}</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
