import { useEffect, useState } from "react";
import { AddressPick } from "@/components/AddressPick";
import { useQueryClient } from "@tanstack/react-query";
import { Check, X, AlertTriangle, FolderSearch, Activity, KeyRound, HeartPulse, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { api, errMsg } from "@/lib/api";
import { DownloadLink } from "@/components/DownloadButton";
import { ExtrasCard } from "@/components/ExtrasCard";
import { markNewCareer } from "@/components/Tour";
import { ClubPicker } from "@/components/ClubPicker";

const STEPS = [["Find FM", FolderSearch], ["Match analytics", Activity], ["DOF key", KeyRound], ["Health check", HeartPulse]];
const ICON = { ok: Check, warn: AlertTriangle, fail: X };

const StepBar = ({ step, go }) => (
  <div className="steps">
    {STEPS.map(([label, Icon], i) => {
      const back = i < step && step < 3;
      return (
      <button type="button" key={label} className={`stp${i === step ? " on" : ""}${i < step ? " done" : ""}${back ? " stp-back" : ""}`} disabled={!back} onClick={() => back && go(i)} title={back ? `Go back to ${label}` : undefined} aria-current={i === step ? "step" : undefined} data-testid={`setup-step-${i + 1}`}>
        <i>{i < step ? <Check size={14} /> : i + 1}</i><Icon size={18} />{label}
      </button>
      );
    })}
  </div>
);

const BackBtn = ({ back, id }) => <button className="btn btn-l" onClick={back} data-testid={`setup-back-${id}`}>Back</button>;

export const CheckList = ({ items, id }) => (
  <div className="checks" data-testid={id}>
    {items.map((it) => { const I = ICON[it.status]; return (
      <div key={it.key} className={`chk ${it.status}`} data-testid={`${id}-${it.key}`}>
        <span className="chk-i"><I size={16} /></span>
        <div><b>{it.label}</b><small>{it.detail}</small>{it.fix && <small className="chk-fix">{it.fix}</small>}</div>
      </div>); })}
  </div>
);

const Head = ({ title, text }) => (<><h2 className="ttl" style={{ justifyContent: "center", textAlign: "center" }}>{title}</h2><p className="note" style={{ textAlign: "center" }}>{text}</p></>);

const careerName = (club, edition) => `${club} ${(edition || "").slice(-2)}`.trim();

export const SaveList = ({ saves, pick, onPick }) => (
  <div className="save-list" role="radiogroup" aria-label="Saves found on this PC" data-testid="setup-save-list">
    {saves.map((s, i) => <button key={s.path} role="radio" aria-checked={pick === s.path} className={`save-opt${pick === s.path ? " on" : ""}`} onClick={() => onPick(s)} data-testid={`setup-save-${i}`}>
      <b>{s.name}</b><small>{new Date(s.modified * 1000).toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })} · {s.size_mb} MB</small><small className="mono">{s.folder}</small>
    </button>)}
  </div>
);

const FindStep = ({ form, set, next }) => {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [folder, setFolder] = useState("");
  const [check, setCheck] = useState(null);
  const inspect = async (save_folder) => {
    setBusy(true);
    setCheck(null);
    try {
      const { data } = await api.post("/setup/inspect", { edition: form.edition, save_folder });
      setRes(data);
      const keep = data.saves?.find((s) => s.path === form.save_file) || data.saves?.[0];
      set({ save_folder: keep?.folder || data.save_folder, save_file: keep?.path || "", found: true });
      if (keep) test(keep.path, keep.path === form.save_file ? form.club_uid ?? null : null);
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  const pick = (s) => { set({ save_folder: s.folder, save_file: s.path, club_uid: null }); test(s.path); };
  const test = async (path = form.save_file, club_uid = null) => {
    const prev = check;
    setCheck({ busy: true, clubs: prev?.clubs });
    try {
      const { data } = await api.post("/setup/check-save", { path, club_uid, club_name: form.club_edited ? form.club_name : "" });
      setCheck(data);
      if (data.ok) set({ club_uid: club_uid ?? null, ...(form.club_edited && club_uid == null ? {} : { club_name: data.club_name }), ...(form.name_edited ? {} : { name: careerName(data.club_name, form.edition) }) });
    } catch (e) { setCheck({ ok: false, error: errMsg(e) }); }
  };
  useEffect(() => { if (form.found && !res) inspect(form.save_folder); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const saves = res?.saves || [];
  const ready = res && form.save_file && check?.ok !== false && form.name.trim() && form.club_name.trim() && (form.address || "").trim();
  return (
    <div>
      <Head title="Find your saves" text="FMCC scans this PC for Football Manager saves, including OneDrive Documents folders. Pick the one to use, or type your save folder. In this browser preview it uses sample saves." />
      <div className="wiz-row">
        <div className="seg">
          {["FM26", "FM27"].map((e) => <button key={e} className={form.edition === e ? "on" : ""} onClick={() => { set({ edition: e, found: false }); setRes(null); }} data-testid={`setup-edition-${e.toLowerCase()}`}>{e}</button>)}
        </div>
        <button className="btn btn-g btn-l" onClick={() => inspect()} disabled={busy} data-testid="setup-detect-button">{busy ? <Loader2 size={18} className="animate-spin" /> : <FolderSearch size={18} />}{res ? "Scan again" : "Scan this PC for saves"}</button>
      </div>
      <div className="wiz-row" style={{ marginTop: 10 }} data-testid="setup-choose-folder">
        <input className="inp" style={{ flex: 1 }} placeholder="Or type a save folder, e.g. C:\Users\You\Documents\Sports Interactive\Football Manager 2027\games" value={folder} onChange={(e) => setFolder(e.target.value)} data-testid="setup-folder-input" />
        <button className="btn btn-l" disabled={folder.trim().length < 3 || busy} onClick={() => inspect(folder.trim())} data-testid="setup-choose-folder-button">Search this folder</button>
      </div>
      {res && <>
        <CheckList items={res.items} id="setup-found" />
        {saves.length > 0 && <>
          <label className="lbl" style={{ marginTop: 16 }}>Choose your save ({saves.length} found, newest first)</label>
          <SaveList saves={saves} pick={form.save_file} onPick={pick} />
          <div className="wiz-row" style={{ marginTop: 10 }}>
            <button className="btn" disabled={!form.save_file || check?.busy} onClick={() => test(form.save_file, form.club_uid ?? null)} data-testid="setup-check-save">{check?.busy ? <Loader2 size={15} className="animate-spin" /> : null}{check?.busy ? "Reading the save with both readers… this can take a minute or two" : "Check this save"}</button>
            {check?.ok && <span className="st ok" data-testid="setup-check-ok">Read OK: {check.club_name}, {check.players} players, game date {check.game_date}</span>}
          </div>
          {check?.ok && check.note && <p className="note" style={{ marginTop: 8 }} data-testid="setup-check-note">{check.note}</p>}
          {check?.ok === false && <p className="chk-fix" style={{ marginTop: 8 }} data-testid="setup-check-error">{check.error}</p>}
          {(check?.need_club || (check?.busy && check.clubs)) && <ClubPicker clubs={check.clubs || []} busy={check.busy} onPick={(c) => test(form.save_file, c.uid)} />}
        </>}
        <div className="wiz-2col">
          <div><label className="lbl">Club</label><input className="inp" value={form.club_name} maxLength={60} placeholder="Filled in from your save" onChange={(e) => set({ club_name: e.target.value, club_edited: true })} data-testid="setup-club-input" /></div>
          <div><label className="lbl">Career name</label><input className="inp" value={form.name} maxLength={60} placeholder="Filled in from your save, e.g. Wrexham 27" onChange={(e) => set({ name: e.target.value, name_edited: true })} data-testid="setup-career-input" /></div>
        </div>
        <AddressPick value={form.address} onChange={(address) => set({ address })} />
        <div style={{ marginTop: 24, textAlign: "right" }}><button className="btn btn-p btn-l" disabled={!ready} onClick={next} data-testid="setup-next-1">Continue</button></div>
      </>}
    </div>
  );
};

const AnalyticsStep = ({ form, set, next, back }) => (
  <div>
    <Head title="Match analytics (optional)" text="FMMatchLens records xG, shot maps and player stats from every match you play; it stays off unless you switch it on." />
    <div className="chk ok" style={{ marginTop: 24 }}><div style={{ flex: 1 }}><b>Set up match analytics after setup</b><small>You'll install it from Connections with FM closed. You can change your mind any time.</small></div>
      <Switch checked={!!form.analytics} onCheckedChange={(v) => set({ analytics: v })} data-testid="setup-analytics-switch" /></div>
    <div style={{ marginTop: 24, display: "flex", justifyContent: "space-between" }}><BackBtn back={back} id="2" /><button className="btn btn-p btn-l" onClick={next} data-testid="setup-next-2">Continue</button></div>
  </div>
);

const KeyStep = ({ next, busy, back }) => {
  const [key, setKey] = useState("");
  const [desktop, setDesktop] = useState(false);
  const [res, setRes] = useState(null);
  const [checking, setChecking] = useState(false);
  useEffect(() => { api.get("/dof/status").then((r) => setDesktop(r.data.desktop)).catch(() => {}); }, []);
  const check = async () => {
    setChecking(true); setRes(null);
    try { setRes((await api.post("/setup/check-key", { key: desktop ? key : null })).data); } catch (e) { setRes({ ok: false, error: errMsg(e) }); } finally { setChecking(false); }
  };
  return (
    <div>
      <Head title="Director of Football key (optional)" text={desktop ? "Your own OpenAI key powers the DOF chat. It's stored only on this PC." : "In the browser preview the DOF uses a built-in preview key. You can check it works."} />
      <div className="wiz-row" style={{ justifyContent: "center" }}>
        {desktop && <input className="inp mono" style={{ flex: 1 }} type="password" placeholder="sk-..." value={key} onChange={(e) => { setKey(e.target.value); setRes(null); }} data-testid="setup-key-input" />}
        <button className="btn btn-l" disabled={checking || (desktop && key.trim().length < 20)} onClick={check} data-testid="setup-key-check">{checking ? <Loader2 size={18} className="animate-spin" /> : <KeyRound size={18} />}{desktop ? "Check key" : "Check the preview key"}</button>
      </div>
      {res && <CheckList id="setup-key-result" items={[{ key: "key", label: res.ok ? "Key works" : "Key didn't work", status: res.ok ? "ok" : "fail", detail: res.ok ? res.detail : res.error }]} />}
      <div style={{ marginTop: 24, display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <BackBtn back={back} id="3" />
        <span style={{ marginLeft: "auto" }} />
        <button className="btn btn-l" disabled={busy} onClick={next} data-testid="setup-skip-key">{busy ? <Loader2 size={18} className="animate-spin" /> : null}Skip for now</button>
        <button className="btn btn-p btn-l" disabled={busy || !res?.ok} onClick={next} data-testid="setup-next-3">{busy ? <Loader2 size={18} className="animate-spin" /> : null}Continue</button>
      </div>
    </div>
  );
};

const HealthStep = ({ analytics }) => {
  const qc = useQueryClient();
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/setup/health").then((r) => setItems(r.data.items)).catch((e) => toast.error(errMsg(e))); }, []);
  return (
    <div data-testid="setup-health">
      <Head title="Health check" text="Green is ready, amber needs a look, red needs fixing. Each one says what to do." />
      {items ? <CheckList items={items} id="health" /> : <p className="note" style={{ textAlign: "center", marginTop: 20 }}><Loader2 size={16} className="animate-spin" /></p>}
      {analytics && <p className="note" style={{ textAlign: "center", marginTop: 14 }} data-testid="setup-analytics-reminder">Match analytics: open Connections to install FMMatchLens with FM closed.</p>}
      <div style={{ marginTop: 20 }}><ExtrasCard compact /></div>
      <p className="note" style={{ textAlign: "center", marginTop: 8 }}>You can do this later: the full list is under "Downloads you need" at the top of every page.</p>
      <div style={{ marginTop: 28, textAlign: "center" }}><button className="btn btn-g btn-l" disabled={!items} onClick={() => qc.invalidateQueries()} data-testid="setup-finish-button">Open FMCC</button></div>
    </div>
  );
};

export default function Setup({ restart }) {
  const qc = useQueryClient();
  const cancel = async () => { try { await api.post("/setup/cancel"); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); } };
  const [step, setStep] = useState(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ edition: "FM27", save_folder: "", save_file: "", club_name: "", name: "", club_edited: false, name_edited: false, address: "Boss", analytics: false, found: false });
  useEffect(() => { api.get("/setup/progress").then((r) => { setForm((f) => ({ ...f, ...r.data.form })); setStep(Math.min(r.data.step, 2)); }).catch(() => setStep(0)); }, []);
  useEffect(() => { if (step !== null && step < 3) api.put("/setup/progress", { step, form }).catch(() => {}); }, [step, form]);
  const set = (p) => setForm((f) => ({ ...f, ...p }));
  const [fail, setFail] = useState(null);
  const finish = async () => {
    setBusy(true); setFail(null);
    try { await api.post("/setup/complete", { edition: form.edition, save_folder: form.save_folder, save_file: form.save_file || null, club_uid: form.club_uid ?? null, club_name: form.club_name, name: form.name, address: form.address.trim() }); markNewCareer(); setStep(3); }
    catch (e) { setFail(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div className="setup grain" data-testid="setup-page">
      <div className="wiz">
        <img src="/fmcc-logo.png" alt="FMCC" className="wiz-logo rise" data-testid="setup-logo" />
        <h1 className="h rise wiz-h">Welcome to <span className="serif">FMCC.</span></h1>
        <p className="lede wiz-lede">{restart ? "Set up a different save or club. Your other careers and their history stay as they are." : "Four quick steps and your club is ready."}</p>
        {restart && step !== 3 && <button className="btn" style={{ margin: "0 auto 16px", display: "flex" }} onClick={cancel} data-testid="setup-cancel-restart">Cancel and go back to FMCC</button>}
        <div className="setup-dl"><DownloadLink /></div>
        {step !== null && <><StepBar step={step} go={(i) => { setFail(null); setStep(i); }} />
          <div className="card rise d1 wiz-card" data-testid="setup-card">
            {step === 0 && <FindStep form={form} set={set} next={() => setStep(1)} />}
            {step === 1 && <AnalyticsStep form={form} set={set} next={() => setStep(2)} back={() => setStep(0)} />}
            {step === 2 && <KeyStep busy={busy} next={finish} back={() => { setFail(null); setStep(1); }} />}
            {step === 2 && fail && <div className="chk fail" style={{ marginTop: 18 }} data-testid="setup-finish-error"><div style={{ flex: 1 }}><b>FMCC couldn't finish setting up with this save</b><small>{fail}</small></div>
              <button className="btn btn-p" onClick={() => { setFail(null); setStep(0); }} data-testid="setup-pick-another">Pick another save</button></div>}
            {step === 3 && <HealthStep analytics={form.analytics} />}
          </div></>}
      </div>
    </div>
  );
}
