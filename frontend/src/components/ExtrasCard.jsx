import { useEffect, useState } from "react";
import { ExternalLink, Download, RefreshCw, CheckCircle2, CircleAlert, Package } from "lucide-react";
import { api, ago } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const confirmText = (it) => (it.key === "real_name_fix"
  ? "Install the Real Name Fix? FMCC backs up the game's dbc, edt and lnc folders, replaces them with the fix's folders and copies its .fmf files into editor data. Close FM first."
  : it.kind === "installer" ? "Download and start the NG_Regens Manager installer?" : `Install ${it.name}? Files it replaces in FM's graphics folder are backed up first.`);
const WAIT_MS = 30 * 60 * 1000;

const PackButton = ({ it, u, act, desktop, refetch }) => {
  const [wait, setWait] = useState(null);
  const install = () => act(() => api.post(`/extras/${it.key}/install`), (r) => r.message, ["extras", "editor-state"]);
  useEffect(() => {
    if (!wait) { return undefined; }
    if (it.download) { setWait(null); install(); return undefined; }
    if (Date.now() - wait > WAIT_MS) { setWait(null); return undefined; }
    const t = setTimeout(() => refetch(), 5000);
    return () => clearTimeout(t);
  }, [wait, it.download, refetch]); // eslint-disable-line react-hooks/exhaustive-deps
  const go = () => {
    if (!window.confirm(confirmText(it))) { return; }
    if (it.download) { install(); return; }
    if (it.key === "ng_regens" && desktop) { act(() => api.post("/extras/ng_regens/fetch"), (r) => r.message, ["extras", "editor-state"]); return; }
    window.open(it.page, "_blank", "noreferrer");
    setWait(Date.now());
  };
  if (wait) return <span className="note" style={{ display: "flex", gap: 8, alignItems: "center" }} data-testid={`extra-waiting-${it.key}`}><RefreshCw size={13} className="animate-spin" />Waiting for the download…<button className="btn" onClick={() => setWait(null)} data-testid={`extra-cancel-${it.key}`}>Cancel</button></span>;
  if (it.found && it.installed_at && !u?.update) return <span className="st g" data-testid={`extra-installed-${it.key}`}>Installed ✓</span>;
  return <button className="btn btn-g" onClick={go} data-testid={`extra-install-${it.key}`}><Download size={13} />{it.found && u?.update ? "Update" : "Download & install"}</button>;
};

const Update = ({ u }) => {
  if (!u) return null;
  if (u.update) return <small className="st a" data-testid="extra-update-available">Newer version posted: {u.latest}</small>;
  if (u.latest) return <small className="note" data-testid="extra-update-latest">Latest: {u.latest}{u.unknown_installed ? " (install through FMCC so it can tell if yours is older)" : " · you're up to date"}</small>;
  return <small className="note" data-testid="extra-update-manual">{u.message}</small>;
};

const Item = ({ it, u, act, desktop, refetch }) => (
  <div className="row" style={{ alignItems: "flex-start", flexWrap: "wrap", gap: 10 }} data-testid={`extra-${it.key}`}>
    {it.found ? <CheckCircle2 size={18} color="#34D399" style={{ marginTop: 2 }} /> : <CircleAlert size={18} color={it.needed ? "#F87171" : "#94A3B8"} style={{ marginTop: 2 }} />}
    <div style={{ flex: "1 1 260px", minWidth: 0 }}>
      <b>{it.name}</b> <span className={`st ${it.needed ? "r" : "n"}`} data-testid={`extra-need-${it.key}`}>{it.needed ? "Needed" : "Optional"}</span>
      <small>{it.for}. By {it.by}.</small>
      <small data-testid={`extra-status-${it.key}`}>{it.detail}{it.installed_at ? ` · installed by FMCC ${ago(it.installed_at)}` : ""}</small>
      {it.kind !== "app" && <small className="note">{it.how}</small>}
      {it.download && <small data-testid={`extra-download-${it.key}`}>In Downloads: {it.download.file} ({it.download.mb} MB){it.download.sample ? " · SAMPLE file for this preview" : ""}</small>}
      <Update u={u} />
    </div>
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
      <a className="ib" href={it.page} target="_blank" rel="noreferrer" title="Official page" data-testid={`extra-get-${it.key}`}><ExternalLink size={13} /></a>
      <PackButton it={it} u={u} act={act} desktop={desktop} refetch={refetch} />
    </div>
  </div>
);

export const ExtrasCard = ({ compact }) => {
  const { data, refetch } = useGet("extras", "/extras");
  const act = useAct();
  const [upd, setUpd] = useState(null);
  if (!data) return null;
  const items = compact ? data.items.filter((i) => i.kind !== "app") : data.items;
  return (
    <div className="card extras-card" style={{ textAlign: "left" }} data-testid="extras-card">
      <div className="ttl"><Package size={14} />Packs to download<span className={`st ${data.needed_missing.length ? "a" : "g"}`} data-testid="extras-missing">{data.needed_missing.length ? `${data.needed_missing.length} needed pack(s) missing` : "All needed packs found"}</span></div>
      <p className="note" style={{ marginTop: 6 }}>These belong to their authors, so FMCC can't ship them. Press Download & install: FMCC fetches NG_Regens itself; for sortitoutsi packs it opens the official page (sign in there as normal), watches your Downloads folder and installs the file the moment it lands.{!data.desktop && " In this browser preview the downloads are SAMPLE files."}</p>
      <div style={{ marginTop: 8 }}>{items.map((it) => <Item key={it.key} it={it} u={upd?.items[it.key]} act={act} desktop={data.desktop} refetch={refetch} />)}</div>
      <div className="acts" style={{ marginTop: 10 }}>
        <button className="btn" onClick={() => act(() => api.get("/extras/updates")).then((r) => r && setUpd(r))} data-testid="extras-check-updates"><RefreshCw size={13} />Check for pack updates</button>
        {upd && <small className="note" data-testid="extras-checked-at">Checked {ago(upd.checked_at)}</small>}
      </div>
      {!compact && <div style={{ marginTop: 14 }} data-testid="extras-built-in"><div className="eyebrow">Already built into FMCC (nothing to download)</div>
        {data.built_in.map((b) => <small key={b.name} style={{ display: "block" }}>{b.name}: {b.role}</small>)}</div>}
    </div>
  );
};
