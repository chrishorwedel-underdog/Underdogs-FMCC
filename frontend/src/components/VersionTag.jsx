import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Download, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";
import { useGet } from "@/lib/ui";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";

const useInstall = () => {
  const [busy, setBusy] = useState(false);
  const go = async () => {
    setBusy(true);
    try {
      const r = await api.post("/fmcc/install");
      toast.success(`Downloaded FMCC ${r.data.version}. FMCC will close, install it and open again.`);
    } catch (e) { toast.error(errMsg(e)); setBusy(false); }
  };
  return [busy, go];
};

const UpdatePrompt = ({ installed, onClose }) => {
  const { data, isError } = useGet("fmcc-latest", "/fmcc/latest");
  const [busy, go] = useInstall();
  return (
    <div className="upd-pop" data-testid="update-prompt">
      <b data-testid="update-prompt-title">FMCC {data?.version || ""} is ready</b>
      <small style={{ color: "var(--dim)" }}>You have {installed}</small>
      {isError && <small className="note" data-testid="update-prompt-error">Couldn't reach the release page.</small>}
      {data?.items?.length > 0 && <ul data-testid="update-prompt-notes">{data.items.slice(0, 4).map((t) => <li key={t}>{t}</li>)}</ul>}
      {data && !data.can_install && <small className="note" data-testid="update-prompt-manual">One-click update works in the Windows program. Get the installer from Downloads.</small>}
      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
        <button className="btn btn-g" disabled={busy || !data?.can_install} onClick={go} data-testid="update-now-btn">
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}{busy ? "Downloading…" : "Update now"}</button>
        <button className="btn" onClick={onClose} disabled={busy} data-testid="update-later-btn">Not now</button>
      </div>
    </div>
  );
};

export const UpdateCard = () => {
  const { data } = useQuery({ queryKey: ["fmcc-update-card"], queryFn: () => api.get("/fmcc/update-card").then((r) => r.data), staleTime: Infinity, refetchOnWindowFocus: false, retry: false });
  const [shown, setShown] = useState(false);
  const [busy, go] = useInstall();
  useEffect(() => { if (data?.show) { const t = setTimeout(() => setShown(true), 3000); return () => clearTimeout(t); } return undefined; }, [data]);
  if (!data?.show || !shown) return null;
  const later = () => { setShown(false); data.show = false; api.post("/fmcc/update-card/snooze", null, { params: { version: data.version } }).catch(() => {}); };
  return (
    <div className="upd-card" role="status" data-testid="update-card">
      <button className="ib upd-card-x" onClick={later} disabled={busy} aria-label="Not now" data-testid="update-card-close"><X size={13} /></button>
      <b data-testid="update-card-title">FMCC {data.version} is ready</b>
      <small style={{ color: "var(--dim)" }} data-testid="update-card-installed">You have {data.installed}</small>
      {data.items?.length > 0 && <ul data-testid="update-card-notes">{data.items.slice(0, 3).map((t) => <li key={t}>{t}</li>)}</ul>}
      <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
        <button className="btn btn-g" disabled={busy} onClick={go} data-testid="update-card-now">
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}{busy ? "Downloading…" : "Update now"}</button>
        <button className="btn" onClick={later} disabled={busy} data-testid="update-card-later">Not now</button>
      </div>
    </div>
  );
};

export const VersionTag = () => {
  const { data } = useQuery({ queryKey: ["updates"], queryFn: () => api.get("/updates").then((r) => r.data) });
  const [open, setOpen] = useState(false);
  const f = data?.components.find((c) => c.key === "fmcc");
  if (!f) return null;
  const dev = f.installed_version === "dev";
  const label = dev ? "FMCC preview build" : `FMCC ${f.installed_version}`;
  if (dev || f.status !== "update_available") return <NavLink to="/settings" className="tl ver-tag" data-testid="footer-version">{label}</NavLink>;
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="tl ver-tag" title={`FMCC ${f.latest_version} is ready to install`} data-testid="footer-version">{label}<span className="ver-dot" data-testid="footer-update-dot" /></button>
      </PopoverTrigger>
      <PopoverContent side="top" className="w-80">{open && <UpdatePrompt installed={f.installed_version} onClose={() => setOpen(false)} />}</PopoverContent>
    </Popover>
  );
};
