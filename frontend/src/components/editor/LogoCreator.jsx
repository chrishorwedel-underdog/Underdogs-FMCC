import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { api, errMsg } from "@/lib/api";
import { useAct } from "@/lib/ui";

const DRAFT = `${process.env.REACT_APP_BACKEND_URL}/api/editor/drafts/`;
const STYLES = [["classic", "Classic crest"], ["modern", "Modern minimal"], ["roundel", "Retro roundel"], ["animal", "Animal emblem"]];

const Preview = ({ draft }) => (
  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }} data-testid="logo-create-preview">
    {["#0E1117", "#F4F1EA"].map((bg) => (
      <div key={bg} style={{ background: bg, borderRadius: 12, aspectRatio: "1", display: "grid", placeItems: "center", border: "1px solid var(--line)" }}>
        {draft ? <img src={DRAFT + draft} alt="Draft badge" style={{ width: "86%", height: "86%", objectFit: "contain" }} data-testid={`logo-create-draft-${bg === "#0E1117" ? "dark" : "light"}`} />
          : <span style={{ color: bg === "#0E1117" ? "var(--dim)" : "#8a8578", fontSize: 12 }}>Draft appears here</span>}
      </div>))}
  </div>
);

export const LogoCreator = ({ c, onClose }) => {
  const act = useAct();
  const [f, setF] = useState({ colours: ["#C8102E", "#FFFFFF"], style: "classic", notes: "", with_name: true });
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState(null);
  const [err, setErr] = useState(null);
  const name = c.rename?.long || c.name;
  const setCol = (i, v) => setF({ ...f, colours: f.colours.map((x, j) => (j === i ? v : x)) });
  const make = async () => {
    setBusy(true); setErr(null);
    try { const { data } = await api.post(`/editor/clubs/${c.uid}/logo/generate`, f, { timeout: 120000 }); setDraft(data.draft); }
    catch (e) { setErr(errMsg(e)); }
    finally { setBusy(false); }
  };
  const use = async () => {
    const r = await act(() => api.post(`/editor/clubs/${c.uid}/logo/use-draft`, { image: draft }), `New logo for ${name}`, ["editor-clubs", "editor-status"]);
    if (r) onClose();
  };
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl" data-testid="logo-creator">
        <DialogHeader><DialogTitle>Create a badge for {name}</DialogTitle>
          <DialogDescription>ChatGPT designs an original badge from the club's name and your colours. Check the preview on dark and light backgrounds before you use it.</DialogDescription></DialogHeader>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 300px", gap: 18 }}>
          <div style={{ display: "grid", gap: 12, alignContent: "start" }}>
            <div><div className="eyebrow">Club colours</div>
              <div style={{ display: "flex", gap: 10, marginTop: 6, alignItems: "center" }}>
                {f.colours.map((col, i) => <input key={i} type="color" value={col} onChange={(e) => setCol(i, e.target.value)} style={{ width: 44, height: 34, border: 0, background: "none", cursor: "pointer" }} data-testid={`logo-colour-${i}`} />)}
                {f.colours.length < 3 && <button className="btn" onClick={() => setF({ ...f, colours: [...f.colours, "#1B2A4A"] })} data-testid="logo-colour-add">Add colour</button>}
                {f.colours.length > 1 && <button className="btn" onClick={() => setF({ ...f, colours: f.colours.slice(0, -1) })} data-testid="logo-colour-remove">Remove</button>}
              </div></div>
            <div><div className="eyebrow">Style</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>{STYLES.map(([k, l]) => (
                <button key={k} className={`btn${f.style === k ? " btn-p" : ""}`} onClick={() => setF({ ...f, style: k })} data-testid={`logo-style-${k}`}>{l}</button>))}</div></div>
            <label className="row" style={{ borderTop: 0, padding: 0 }}><div style={{ flex: 1 }}>Put the club's name on the badge<small>AI lettering can come out misspelled; check the preview.</small></div>
              <Switch checked={f.with_name} onCheckedChange={(v) => setF({ ...f, with_name: v })} data-testid="logo-with-name" /></label>
            <textarea className="inp" rows={3} maxLength={300} style={{ height: "auto", padding: 10 }} placeholder="e.g. a lighthouse, two stars above the shield, founded 1898" value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} data-testid="logo-create-notes" />
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <button className="btn btn-p" disabled={busy} onClick={make} data-testid="logo-create-generate">{busy ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}{draft ? "Try again" : "Create badge"}</button>
              {busy && <span className="note">This can take up to a minute…</span>}
            </div>
            {err && <p className="note" style={{ color: "var(--red)" }} data-testid="logo-create-error">{err}</p>}
          </div>
          <div style={{ display: "grid", gap: 10, alignContent: "start" }}>
            <Preview draft={draft} />
            <button className="btn btn-p" disabled={!draft || busy} onClick={use} data-testid="logo-create-use">Use this logo</button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
