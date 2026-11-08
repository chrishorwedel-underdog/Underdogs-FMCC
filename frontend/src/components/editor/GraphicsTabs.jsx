import { useRef, useState, useEffect } from "react";
import { Upload, Sparkles, Trash2, Check, Undo2, FileUp, ShieldCheck } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const B = process.env.REACT_APP_BACKEND_URL;
const SLOTS = ["home", "away", "third"];
const TEMPLATES = ["plain", "stripes", "hoops", "sash", "halves", "quarters", "pinstripes", "chevron"];
const KEYS = ["editor-kits", "editor-status", "packs", "pack-check"];

const KitCard = ({ c, slot, pick, onUse }) => {
  const act = useAct();
  const file = useRef(null);
  const k = c.kits[slot];
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post(`/editor/kits/${c.uid}/${slot}`, fd), `${slot} kit saved`, KEYS); };
  return (
    <div style={{ textAlign: "center" }} data-testid={`kit-${c.uid}-${slot}`}>
      <div style={{ height: 110, borderRadius: 10, background: "var(--s1)", border: "1px solid var(--line)", display: "grid", placeItems: "center", overflow: "hidden" }}>
        {k ? <img src={`${B}/api/editor/kit-image/${c.uid}/${slot}?v=${k.image}`} alt={`${c.name} ${slot}`} style={{ maxHeight: 104 }} /> : <small style={{ color: "var(--dim)" }}>No {slot} kit</small>}
      </div>
      <input ref={file} type="file" accept="image/png,image/jpeg" hidden onChange={(e) => { if (e.target.files[0]) upload(e.target.files[0]); e.target.value = ""; }} />
      <div style={{ display: "flex", gap: 4, justifyContent: "center", marginTop: 6 }}>
        <button className="btn" title="Upload" onClick={() => file.current.click()} data-testid={`kit-upload-${c.uid}-${slot}`}><Upload size={12} /></button>
        <button className="btn" title="Create with ChatGPT" onClick={() => pick(c, slot)} data-testid={`kit-create-${c.uid}-${slot}`}><Sparkles size={12} /></button>
        {k && <button className="btn btn-d" title="Remove" onClick={() => act(() => api.delete(`/editor/kits/${c.uid}/${slot}`), `${slot} kit removed`, KEYS)} data-testid={`kit-remove-${c.uid}-${slot}`}><Trash2 size={12} /></button>}
      </div>
      {onUse}
    </div>
  );
};

const Creator = ({ target, close }) => {
  const [f, setF] = useState({ colours: ["#C8102E", "#FFFFFF"], template: "plain", notes: "" });
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const act = useAct();
  const gen = async () => { setBusy(true); const r = await act(() => api.post(`/editor/kits/${target.c.uid}/${target.slot}/generate`, f)); if (r) setDraft(r.draft); setBusy(false); };
  return (
    <div className="card" style={{ padding: 14 }} data-testid="kit-creator">
      <div className="ttl"><Sparkles size={14} />{target.slot} kit for {target.c.name}<span style={{ marginLeft: "auto" }} /><button className="btn" onClick={close} data-testid="kit-creator-close">Close</button></div>
      <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
        {f.colours.map((col, i) => <input key={i} type="color" value={col} onChange={(e) => setF({ ...f, colours: f.colours.map((x, j) => (j === i ? e.target.value : x)) })} data-testid={`kit-colour-${i}`} />)}
        {f.colours.length < 3 && <button className="btn" onClick={() => setF({ ...f, colours: [...f.colours, "#111111"] })} data-testid="kit-colour-add">+ colour</button>}
        <select className="inp" style={{ width: 150 }} value={f.template} onChange={(e) => setF({ ...f, template: e.target.value })} data-testid="kit-template">{TEMPLATES.map((t) => <option key={t}>{t}</option>)}</select>
        <input className="inp" style={{ flex: 1, minWidth: 160 }} placeholder="Details (optional)" maxLength={300} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} data-testid="kit-notes" />
        <button className="btn btn-p" disabled={busy} onClick={gen} data-testid="kit-generate">{busy ? "Creating…" : "Create"}</button>
      </div>
      {draft && <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 12 }}>
        <img src={`${B}/api/editor/drafts/${draft}`} alt="Draft kit" style={{ height: 160, borderRadius: 10, background: "var(--s1)" }} data-testid="kit-draft-image" />
        <button className="btn btn-p" onClick={() => act(() => api.post(`/editor/kits/${target.c.uid}/${target.slot}/use-draft`, { image: draft }), "Kit saved", KEYS).then((r) => r && close())} data-testid="kit-use-draft"><Check size={13} />Use this kit</button></div>}
    </div>
  );
};

const BulkKits = ({ clubs }) => {
  const [sel, setSel] = useState([]);
  const [slot, setSlot] = useState("home");
  const [template, setTemplate] = useState("plain");
  const [job, setJob] = useState(null);
  const act = useAct();
  const qc = useQueryClient();
  useEffect(() => {
    if (!job || job.done) { return undefined; }
    const t = setInterval(() => api.get(`/editor/kits/bulk/${job.id}`).then((r) => setJob(r.data)), 2500);
    return () => clearInterval(t);
  }, [job]);
  const start = async () => { const r = await act(() => api.post("/editor/kits/bulk", { uids: sel, slot, template, colours: ["#1F4E9E", "#FFFFFF"] })); if (r) setJob(r); };
  return (
    <div className="card" style={{ padding: 14 }} data-testid="bulk-kits">
      <div className="ttl"><Sparkles size={14} />Bulk ChatGPT kits<span className="st n">up to 10 clubs</span></div>
      <p className="note" style={{ marginTop: 4 }}>Each kit is created one after another as a draft. Nothing changes until you press Use on it.</p>
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        <select className="inp" style={{ width: 120 }} value={slot} onChange={(e) => setSlot(e.target.value)} data-testid="bulk-kit-slot">{SLOTS.map((s) => <option key={s}>{s}</option>)}</select>
        <select className="inp" style={{ width: 150 }} value={template} onChange={(e) => setTemplate(e.target.value)} data-testid="bulk-kit-template">{TEMPLATES.map((t) => <option key={t}>{t}</option>)}</select>
        <button className="btn btn-p" disabled={!sel.length || (job && !job.done)} onClick={start} data-testid="bulk-kit-start">Create {sel.length} kit(s)</button>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>{clubs.slice(0, 30).map((c) => <label key={c.uid} className="tag st n" style={{ cursor: "pointer", color: sel.includes(c.uid) ? "var(--acc)" : undefined }}>
        <input type="checkbox" checked={sel.includes(c.uid)} onChange={() => setSel(sel.includes(c.uid) ? sel.filter((x) => x !== c.uid) : [...sel, c.uid].slice(0, 10))} data-testid={`bulk-kit-club-${c.uid}`} /> {c.name}</label>)}</div>
      {job && <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(150px,1fr))", gap: 10, marginTop: 12 }} data-testid="bulk-kit-results">{job.items.map((i) => (
        <div key={i.uid} className="card" style={{ padding: 8, textAlign: "center" }}><small>{i.name}</small>
          {i.draft ? <img src={`${B}/api/editor/drafts/${i.draft}`} alt={i.name} style={{ height: 90, display: "block", margin: "6px auto" }} /> : <div className="note" style={{ height: 90, display: "grid", placeItems: "center" }}>{i.status}{i.error ? `: ${i.error}` : ""}</div>}
          {i.draft && <button className="btn btn-p" onClick={() => act(() => api.post(`/editor/kits/${i.uid}/${job.slot}/use-draft`, { image: i.draft }), `Kit saved for ${i.name}`, KEYS).then(() => qc.invalidateQueries({ queryKey: ["editor-kits"] }))} data-testid={`bulk-kit-use-${i.uid}`}>Use</button>}
        </div>))}</div>}
    </div>
  );
};

export const KitsTab = () => {
  const [q, setQ] = useState("");
  const [target, setTarget] = useState(null);
  const { data = [] } = useGet("editor-kits", "/editor/kits", { q });
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="kits-tab">
      <input className="inp" style={{ maxWidth: 320 }} placeholder="Find a club" value={q} onChange={(e) => setQ(e.target.value)} data-testid="kits-search" />
      {target && <Creator target={target} close={() => setTarget(null)} />}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(360px,1fr))", gap: 12 }}>{data.map((c) => (
        <div key={c.uid} className="card" style={{ padding: 12 }} data-testid={`kits-club-${c.uid}`}>
          <div className="ttl">{c.name}<span className="st n">{c.league}</span></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, marginTop: 8 }}>{SLOTS.map((s) => <KitCard key={s} c={c} slot={s} pick={(cl, sl) => setTarget({ c: cl, slot: sl })} />)}</div>
        </div>))}</div>
      <BulkKits clubs={data} />
      <p className="note">Kits are written to FMCC's own graphics folder as club/ID/kits/home, away and third. Check them in FM after the next graphics reload.</p>
    </div>
  );
};

export const PacksTab = () => {
  const { data: packs = [] } = useGet("packs", "/editor/packs");
  const [pack, setPack] = useState(null);
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const { data } = useGet("pack", `/editor/packs/${encodeURIComponent(pack)}`, { q, offset, limit: 60 }, { enabled: !!pack });
  return (
    <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 16 }} data-testid="packs-tab">
      <div className="card">{packs.map((p) => <div key={p.name} className="row" style={{ cursor: "pointer", color: pack === p.name ? "var(--acc)" : undefined }} onClick={() => { setPack(p.name); setOffset(0); }} data-testid={`pack-${p.name}`}>
        <div style={{ flex: 1 }}>{p.name}<small>{p.faces} faces · {p.logos} logos · {p.kits} kits</small></div></div>)}
        {!packs.length && <p className="note">No graphics packs found.</p>}</div>
      <div className="card">{!pack ? <div className="soon">Pick a pack to see every picture with the player or club it belongs to.</div> : <>
        <div className="ttl">{pack}<span className="st n">{data?.total ?? 0} pictures</span><span style={{ marginLeft: "auto" }} /><input className="inp" style={{ width: 200 }} placeholder="Name or ID" value={q} onChange={(e) => { setQ(e.target.value); setOffset(0); }} data-testid="pack-search" /></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(110px,1fr))", gap: 10, marginTop: 10 }} data-testid="pack-grid">{data?.rows.map((r) => (
          <div key={r.index} style={{ textAlign: "center" }} data-testid={`pack-pic-${r.index}`}>
            <img src={`${B}/api/editor/packs/${encodeURIComponent(pack)}/picture/${r.index}`} alt={r.owner || r.to} loading="lazy" style={{ width: 90, height: 90, objectFit: "contain", background: "var(--s1)", borderRadius: 8 }} />
            <small style={{ display: "block", fontSize: 11, color: r.owner ? "var(--mut)" : "var(--red)" }}>{r.owner || "Not in this save"}</small><small className="mono" style={{ fontSize: 10, color: "var(--dim)" }}>{r.uid} · {r.what}</small></div>))}</div>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}><button className="btn" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 60))} data-testid="pack-prev">Previous</button>
          <button className="btn" disabled={!data || offset + 60 >= data.total} onClick={() => setOffset(offset + 60)} data-testid="pack-next">Next</button></div></>}
      </div>
    </div>
  );
};

export const BulkImportTab = () => {
  const [kind, setKind] = useState("faces");
  const [stage, setStage] = useState(null);
  const act = useAct();
  const file = useRef(null);
  const upload = async (files) => { const fd = new FormData(); fd.append("kind", kind); [...files].forEach((f) => fd.append("files", f)); const r = await act(() => api.post("/editor/bulk/stage", fd), "Pictures staged. Nothing is written yet."); if (r) setStage(r); };
  const write = async () => { const r = await act(() => api.post(`/editor/bulk/${stage.id}/write`), "Written to FM", KEYS); if (r) setStage({ ...r, items: stage.items.map((i) => ({ ...i, written: ["add", "replace"].includes(i.status) })) }); };
  const undo = async (n) => { const r = await act(() => api.post(`/editor/bulk/${stage.id}/undo/${n}`), "Picture undone", KEYS); if (r) setStage({ ...stage, items: stage.items.map((i) => (i.n === n ? { ...i, undone: true } : i)) }); };
  const LABEL = { add: ["Will be added", "ok"], replace: ["Will replace", "a"], not_in_save: ["ID not in this save", "r"], skipped: ["Skipped", "n"] };
  return (
    <div className="card" data-testid="bulk-import-tab">
      <div className="ttl"><FileUp size={14} />Bulk import a folder or zip</div>
      <p className="note" style={{ marginTop: 4, lineHeight: 1.6 }}>Files are matched by the ID in their name: a player ID or r-ID for faces, a club ID for logos and kits. Kit files also need home, away or third in the name. Up to 5,000 pictures and 500 MB, each up to 5 MB.</p>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <div className="seg">{[["faces", "Faces"], ["logos", "Logos"], ["kits", "Kits"]].map(([k, l]) => <button key={k} className={kind === k ? "on" : ""} onClick={() => setKind(k)} data-testid={`bulk-kind-${k}`}>{l}</button>)}</div>
        <input ref={file} type="file" multiple accept=".png,.jpg,.jpeg,.zip" hidden onChange={(e) => { if (e.target.files.length) upload(e.target.files); e.target.value = ""; }} data-testid="bulk-file-input" />
        <button className="btn btn-p" onClick={() => file.current.click()} data-testid="bulk-choose"><Upload size={13} />Choose pictures or a zip</button>
      </div>
      {stage && <div style={{ marginTop: 14 }} data-testid="bulk-stage">
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>{Object.entries(stage.counts).map(([k, v]) => <span key={k} className={`st ${LABEL[k][1]}`} data-testid={`bulk-count-${k}`}>{LABEL[k][0]}: {v}</span>)}
          <span style={{ marginLeft: "auto" }} />{stage.state === "staged" && <button className="btn btn-p" disabled={!(stage.counts.add || stage.counts.replace)} onClick={write} data-testid="bulk-write">Write to FM</button>}
          {stage.state === "written" && <span className="st ok" data-testid="bulk-written">Written</span>}</div>
        <div style={{ maxHeight: 420, overflowY: "auto", marginTop: 8 }}>{stage.items.slice(0, 300).map((i) => (
          <div key={i.n} className="row" data-testid={`bulk-item-${i.n}`}>
            {i.image ? <img src={`${B}/api/editor/bulk-image/${i.image}`} alt={i.file} style={{ width: 40, height: 40, objectFit: "contain" }} /> : <span style={{ width: 40 }} />}
            <div style={{ flex: 1 }}>{i.file}<small>{i.owner || (i.uid ? `ID ${i.uid}` : "")}{i.slot ? ` · ${i.slot}` : ""}{i.problem ? ` · ${i.problem}` : ""}</small></div>
            <span className={`st ${LABEL[i.status][1]}`}>{LABEL[i.status][0]}</span>
            {i.written && !i.undone && <button className="btn" onClick={() => undo(i.n)} title="Undo this picture" data-testid={`bulk-undo-${i.n}`}><Undo2 size={12} /></button>}
            {i.undone && <span className="st n">Undone</span>}
          </div>))}</div>
      </div>}
    </div>
  );
};

const Section = ({ title, rows, k, render }) => (
  <div className="card" data-testid={`check-${k}`}><div className="ttl">{title}<span className={`st ${rows.length ? "a" : "ok"}`}>{rows.length}</span></div>
    {rows.slice(0, 50).map((r, i) => <div key={i} className="row" style={{ fontSize: 12.5 }}>{render(r)}</div>)}
    {!rows.length && <p className="note" style={{ marginTop: 6 }}>None found.</p>}</div>
);

export const PackCheckTab = () => {
  const [run, setRun] = useState(false);
  const { data, isFetching, refetch } = useGet("pack-check", "/editor/pack-check", undefined, { enabled: run });
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="pack-check-tab">
      <div className="card"><div className="ttl"><ShieldCheck size={14} />Check my graphics packs</div>
        <p className="note" style={{ marginTop: 4 }}>Scans every pack (NG_Regens, logo packs, kit packs and FMCC's own). It only reports: FMCC never edits another pack's files.</p>
        <button className="btn btn-p" style={{ marginTop: 8 }} disabled={isFetching} onClick={() => (run ? refetch() : setRun(true))} data-testid="pack-check-run">{isFetching ? "Checking…" : "Check now"}</button>
        {data && <p className="note" style={{ marginTop: 8 }} data-testid="pack-check-summary">{data.packs.length} packs · {data.packs.reduce((a, p) => a + p.pictures, 0)} pictures · {data.checked_files} files opened. {data.note}</p>}</div>
      {data && <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Section title="Missing pictures" k="missing" rows={data.missing} render={(r) => <><b>{r.pack}</b><span className="mono" style={{ marginLeft: "auto" }}>{r.file}</span></>} />
        <Section title="Broken pictures" k="broken" rows={data.broken} render={(r) => <><b>{r.pack}</b><span className="mono" style={{ marginLeft: "auto" }}>{r.file}</span></>} />
        <Section title="Set by more than one pack" k="conflicts" rows={data.conflicts} render={(r) => <><span className="mono">{r.to}</span><small style={{ marginLeft: "auto" }}>{r.packs.join(", ")} · likely shown: {r.likely_shown}</small></>} />
        <Section title="IDs not in this save" k="not_in_save" rows={data.not_in_save} render={(r) => <><b>{r.pack}</b><span className="mono" style={{ marginLeft: "auto" }}>{r.to}</span></>} />
      </div>}
    </div>
  );
};
