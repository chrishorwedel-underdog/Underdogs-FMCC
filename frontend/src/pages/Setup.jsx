import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, X, AlertTriangle, FolderSearch, Activity, KeyRound, HeartPulse, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { api, errMsg } from "@/lib/api";
import { DownloadButton } from "@/components/DownloadButton";
import { ExtrasCard } from "@/components/ExtrasCard";

const STEPS = [["Find FM", FolderSearch], ["Match analytics", Activity], ["DOF key", KeyRound], ["Health check", HeartPulse]];
const ICON = { ok: Check, warn: AlertTriangle, fail: X };

const StepBar = ({ step }) => (
  <div className="steps">
    {STEPS.map(([label, Icon], i) => (
      <div key={label} className={`stp${i === step ? " on" : ""}${i < step ? " done" : ""}`} data-testid={`setup-step-${i + 1}`}>
        <i>{i < step ? <Check size={14} /> : i + 1}</i><Icon size={18} />{label}
      </div>
    ))}
  </div>
);

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

const FindStep = ({ form, set, next }) => {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [folder, setFolder] = useState("");
  const inspect = async (save_folder) => {
    setBusy(true);
    try { const { data } = await api.post("/setup/inspect", { edition: form.edition, save_folder }); setRes(data); set({ save_folder: data.save_folder, found: true }); }
    catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  useEffect(() => { if (form.found && !res) inspect(form.save_folder); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const bad = res?.items.some((i) => i.status === "fail");
  const ready = res && res.items.find((i) => i.key === "saves")?.status === "ok" && form.name.trim() && form.club_name.trim();
  return (
    <div>
      <Head title="Find Football Manager" text="FMCC finds FM and your save folder for you. In this browser preview it uses a sample save instead of your PC." />
      <div className="wiz-row">
        <div className="seg">
          {["FM26", "FM27"].map((e) => <button key={e} className={form.edition === e ? "on" : ""} onClick={() => { set({ edition: e, found: false }); setRes(null); }} data-testid={`setup-edition-${e.toLowerCase()}`}>{e}</button>)}
        </div>
        <button className="btn btn-g btn-l" onClick={() => inspect()} disabled={busy} data-testid="setup-detect-button">{busy ? <Loader2 size={18} className="animate-spin" /> : <FolderSearch size={18} />}{res ? "Find again" : `Find ${form.edition}`}</button>
      </div>
      {res && <>
        <CheckList items={res.items} id="setup-found" />
        {bad && <div className="wiz-row" style={{ marginTop: 14 }} data-testid="setup-choose-folder">
          <input className="inp" style={{ flex: 1 }} placeholder="Path to your FM 'games' folder" value={folder} onChange={(e) => setFolder(e.target.value)} data-testid="setup-folder-input" />
          <button className="btn btn-l" disabled={folder.trim().length < 3 || busy} onClick={() => inspect(folder.trim())} data-testid="setup-choose-folder-button">Choose folder</button>
        </div>}
        <div className="wiz-2col">
          <div><label className="lbl">Club</label><input className="inp" value={form.club_name} maxLength={60} onChange={(e) => set({ club_name: e.target.value })} data-testid="setup-club-input" /></div>
          <div><label className="lbl">Career name</label><input className="inp" value={form.name} maxLength={60} onChange={(e) => set({ name: e.target.value })} data-testid="setup-career-input" /></div>
        </div>
        <div style={{ marginTop: 24, textAlign: "right" }}><button className="btn btn-p btn-l" disabled={!ready} onClick={next} data-testid="setup-next-1">Continue</button></div>
      </>}
    </div>
  );
};

const AnalyticsStep = ({ form, set, next }) => (
  <div>
    <Head title="Match analytics (optional)" text="FMMatchLens records xG, shot maps and player stats from every match you play; it stays off unless you switch it on." />
    <div className="chk ok" style={{ marginTop: 24 }}><div style={{ flex: 1 }}><b>Set up match analytics after setup</b><small>You'll install it from Connections with FM closed. You can change your mind any time.</small></div>
      <Switch checked={!!form.analytics} onCheckedChange={(v) => set({ analytics: v })} data-testid="setup-analytics-switch" /></div>
    <div style={{ marginTop: 24, textAlign: "right" }}><button className="btn btn-p btn-l" onClick={next} data-testid="setup-next-2">Continue</button></div>
  </div>
);

const KeyStep = ({ next, busy }) => {
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
      <div style={{ marginTop: 24, display: "flex", justifyContent: "space-between" }}>
        <button className="btn btn-l" disabled={busy} onClick={next} data-testid="setup-skip-key">Skip for now</button>
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

export default function Setup() {
  const [step, setStep] = useState(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ edition: "FM27", save_folder: "", club_name: "Sample Club FC", name: "My first career", analytics: false, found: false });
  useEffect(() => { api.get("/setup/progress").then((r) => { setForm((f) => ({ ...f, ...r.data.form })); setStep(Math.min(r.data.step, 2)); }).catch(() => setStep(0)); }, []);
  useEffect(() => { if (step !== null && step < 3) api.put("/setup/progress", { step, form }).catch(() => {}); }, [step, form]);
  const set = (p) => setForm((f) => ({ ...f, ...p }));
  const finish = async () => {
    setBusy(true);
    try { await api.post("/setup/complete", { edition: form.edition, save_folder: form.save_folder, club_name: form.club_name, name: form.name }); setStep(3); }
    catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div className="setup grain" data-testid="setup-page">
      <div className="wiz">
        <img src="/fmcc-logo.png" alt="FMCC" className="wiz-logo rise" data-testid="setup-logo" />
        <h1 className="h rise wiz-h">Welcome to <span className="serif">FMCC.</span></h1>
        <p className="lede wiz-lede">Four quick steps and your club is ready.</p>
        <DownloadButton />
        {step !== null && <><StepBar step={step} />
          <div className="card rise d1 wiz-card" data-testid="setup-card">
            {step === 0 && <FindStep form={form} set={set} next={() => setStep(1)} />}
            {step === 1 && <AnalyticsStep form={form} set={set} next={() => setStep(2)} />}
            {step === 2 && <KeyStep busy={busy} next={finish} />}
            {step === 3 && <HealthStep analytics={form.analytics} />}
          </div></>}
      </div>
    </div>
  );
}
