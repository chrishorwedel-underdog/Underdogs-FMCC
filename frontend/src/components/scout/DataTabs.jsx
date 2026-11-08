import { useRef, useState } from "react";
import { FileUp, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const KEYS = ["possession", "scout-players", "scatter", "scout-meta", "html-imports"];

const PossRow = ({ r }) => {
  const act = useAct();
  const [v, setV] = useState(r.value ?? "");
  const save = () => { if (String(v) !== String(r.value ?? "")) act(() => api.put(`/scout/possession/${encodeURIComponent(r.club)}`, { value: v === "" ? null : Number(v) }), `${r.club} possession saved`, KEYS); };
  return (
    <div className="row" data-testid={`poss-row-${r.club}`}>
      <div style={{ flex: 1 }}>{r.club}{r.own && <span className="tag st g">Your club</span>}<small>{r.revision ? `${r.revision} version(s) kept` : "Not entered"}</small></div>
      <input className="inp mono" style={{ width: 90, height: 32 }} type="number" min="20" max="80" placeholder="%" value={v} onChange={(e) => setV(e.target.value)} onBlur={save} data-testid={`poss-input-${r.club}`} />
    </div>
  );
};

export const PossessionTab = () => {
  const { data } = useGet("possession", "/scout/possession");
  if (!data) return null;
  const ours = data.rows.find((r) => r.own);
  return (
    <div className="card" style={{ maxWidth: 680 }} data-testid="possession-tab">
      <div className="ttl">Club possession</div>
      <p className="note" style={{ marginTop: 4, lineHeight: 1.6 }}>Attacking stats are multiplied by your possession ÷ his club's; defensive stats by his club's ÷ yours. Percentage stats aren't adjusted.
        {!ours?.value && " Enter your own club's possession first: until then nothing is adjusted."} {data.matchlens}</p>
      <div style={{ marginTop: 8 }}>{data.rows.map((r) => <PossRow key={`${r.club}-${r.revision}`} r={r} />)}</div>
    </div>
  );
};

export const ImportTab = () => {
  const { data = [] } = useGet("html-imports", "/scout/imports");
  const act = useAct();
  const file = useRef(null);
  const upload = (files) => { const fd = new FormData(); [...files].forEach((f) => fd.append("files", f)); act(() => api.post("/scout/import-html", fd), (r) => `${r.players} players imported (${r.linked} linked by UID)`, KEYS); };
  return (
    <div className="card" style={{ maxWidth: 760 }} data-testid="html-import-tab">
      <div className="ttl">Import FM's HTML exports</div>
      <p className="note" style={{ marginTop: 4, lineHeight: 1.6 }}>For when the save can't be read. In FM, select a player view, press Ctrl+P and choose Web page. Add a UID column so FMCC can link each row to the right player; rows without one stay "Not linked" and are never merged with a save player. You can import several files at once.</p>
      <input ref={file} type="file" accept=".html,.htm" multiple hidden onChange={(e) => { if (e.target.files.length) upload(e.target.files); e.target.value = ""; }} data-testid="html-import-input" />
      <button className="btn btn-p" style={{ marginTop: 10 }} onClick={() => file.current.click()} data-testid="html-import-button"><FileUp size={14} />Choose HTML files</button>
      <div style={{ marginTop: 12 }}>{data.map((r) => (
        <div key={r.id} className="row" data-testid={`html-import-${r.id}`}>
          <div style={{ flex: 1 }}>{r.files.join(", ")}<small>{r.count} players · {r.status === "active" ? "in use" : "removed"}</small></div>
          {r.status === "active" && <button className="btn btn-d" onClick={() => act(() => api.delete(`/scout/imports/${r.id}`), "Import removed", KEYS)} data-testid={`html-import-remove-${r.id}`}><Trash2 size={13} /></button>}
        </div>))}</div>
      {data.length > 0 && <p className="note" style={{ marginTop: 8 }}>Imported players show under Players → HTML imports.</p>}
    </div>
  );
};
