import { useEffect, useState } from "react";
import { Check, Sparkles, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg } from "@/lib/api";
import { useGet, useAct, TabBar } from "@/lib/ui";

const SRC = `${process.env.REACT_APP_BACKEND_URL}/api/editor/ng-picture?path=`;
const DRAFT = `${process.env.REACT_APP_BACKEND_URL}/api/editor/drafts/`;
const PAGE = 60;

const Create = ({ player, onClose }) => {
  const act = useAct();
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState(null);
  const [err, setErr] = useState(null);
  const make = async () => {
    setBusy(true); setErr(null);
    try { const { data } = await api.post(`/editor/faces/${player.unique_id}/generate`, { notes }, { timeout: 120000 }); setDraft(data.draft); }
    catch (e) { setErr(errMsg(e)); }
    finally { setBusy(false); }
  };
  const use = async () => {
    const r = await act(() => api.post(`/editor/faces/${player.unique_id}/use-draft`, { image: draft }), `New face for ${player.name}`, ["editor-players", "editor-status", "editor-players-missing"]);
    if (r) onClose();
  };
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 220px", gap: 18 }} data-testid="face-create">
      <div>
        <p className="note">ChatGPT draws a made-up person who fits a {player.age}-year-old from {player.nationality}, in a facepack style. Add anything you'd like, such as hair, beard or skin tone.</p>
        <textarea className="inp" rows={3} maxLength={300} style={{ marginTop: 10, height: "auto", padding: 10 }} placeholder="e.g. short curly black hair, light beard" value={notes} onChange={(e) => setNotes(e.target.value)} data-testid="face-create-notes" />
        <div style={{ display: "flex", gap: 10, marginTop: 10, alignItems: "center" }}>
          <button className="btn btn-p" disabled={busy} onClick={make} data-testid="face-create-generate">{busy ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}{draft ? "Try again" : "Create face"}</button>
          {busy && <span className="note">This can take up to a minute…</span>}
        </div>
        {err && <p className="note" style={{ color: "var(--red)", marginTop: 8 }} data-testid="face-create-error">{err}</p>}
      </div>
      <div style={{ display: "grid", gap: 10, alignContent: "start" }}>
        <div className="ngtile" style={{ cursor: "default" }}>{draft ? <img src={DRAFT + draft} alt="Draft face" data-testid="face-create-draft" /> : <div style={{ aspectRatio: "1", display: "grid", placeItems: "center", color: "var(--dim)", fontSize: 12 }}>Draft appears here</div>}</div>
        <button className="btn btn-p" disabled={!draft || busy} onClick={use} data-testid="face-create-use">Use this face</button>
      </div>
    </div>
  );
};

const Tile = ({ pic, on, onClick }) => (
  <button type="button" onClick={onClick} className={`ngtile${on ? " on" : ""}`} title={pic.used_by ? `Used by ${pic.used_by}` : pic.id} data-testid={`ng-pic-${pic.id}`}>
    <img src={SRC + encodeURIComponent(pic.id)} alt={pic.id} loading="lazy" />
    {pic.used_by && <span className="used">{pic.used_by}</span>}
    {on && <span className="tick"><Check size={14} /></span>}
  </button>
);

export const FacePicker = ({ player, folders, defaultFolder, onClose }) => {
  const [tab, setTab] = useState(folders.length ? "ng" : "ai");
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-4xl" data-testid="face-picker">
        <DialogHeader><DialogTitle>Pick a face for {player.name}</DialogTitle>
          <DialogDescription>{player.nationality} · {player.club}</DialogDescription></DialogHeader>
        <TabBar id="face-picker" value={tab} onChange={setTab} tabs={[...(folders.length ? [["ng", "NG_Regens"]] : []), ["ai", "Create with ChatGPT"]]} />
        {tab === "ng" ? <Browse player={player} folders={folders} defaultFolder={defaultFolder} onClose={onClose} /> : <Create player={player} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  );
};

const Browse = ({ player, folders, defaultFolder, onClose }) => {
  const act = useAct();
  const [folder, setFolder] = useState(defaultFolder || folders[0]);
  const [offset, setOffset] = useState(0);
  const [sel, setSel] = useState(null);
  useEffect(() => { setOffset(0); setSel(null); }, [folder]);
  const { data } = useGet("ng-folder", `/editor/ng-folder/${encodeURIComponent(folder || "")}`, { folder, offset, limit: PAGE }, { enabled: !!folder });
  const use = async () => {
    const r = await act(() => api.post(`/editor/faces/${player.unique_id}/pick`, { path: sel }), `New face for ${player.name}`, ["editor-players", "editor-status", "editor-players-missing", "ng-folder"]);
    if (r) onClose();
  };
  return (
    <>
      <p className="note">Pictures already used by another player are labelled; you can still pick them.</p>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select className="inp" style={{ width: 240, height: 34 }} value={folder} onChange={(e) => setFolder(e.target.value)} data-testid="face-picker-folder">
            {folders.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
          <span className="note" data-testid="face-picker-count">{data ? `${data.total} pictures${data.total > PAGE ? ` · ${offset + 1}–${Math.min(offset + PAGE, data.total)}` : ""}` : "Loading…"}</span>
          <span style={{ marginLeft: "auto" }} />
          <button className="btn" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} data-testid="face-picker-prev">Previous</button>
          <button className="btn" disabled={!data || offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)} data-testid="face-picker-next">Next</button>
        </div>
        <div className="nggrid" data-testid="face-picker-grid">
          {(data?.pictures || []).map((p) => <Tile key={p.id} pic={p} on={sel === p.id} onClick={() => setSel(p.id)} />)}
        </div>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button className="btn" onClick={onClose} data-testid="face-picker-cancel">Cancel</button>
          <button className="btn btn-p" disabled={!sel} onClick={use} data-testid="face-picker-use">Use this face</button>
        </div>
    </>
  );
};
