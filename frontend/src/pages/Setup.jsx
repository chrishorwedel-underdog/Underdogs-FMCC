import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, FolderSearch, Activity, UserRound, KeyRound, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";

const STEPS = [["Find FM", FolderSearch], ["Match analytics", Activity], ["Your career", UserRound], ["OpenAI key", KeyRound]];

const StepBar = ({ step }) => (
  <div className="steps">
    {STEPS.map(([label, Icon], i) => (
      <div key={label} className={`stp${i === step ? " on" : ""}${i < step ? " done" : ""}`} data-testid={`setup-step-${i + 1}`}>
        <i>{i < step ? <Check size={12} /> : i + 1}</i><Icon size={14} />{label}
      </div>
    ))}
  </div>
);

const FindStep = ({ form, set, next }) => {
  const [busy, setBusy] = useState(false);
  const [found, setFound] = useState(false);
  const [edit, setEdit] = useState(false);
  const detect = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/setup/detect", { edition: form.edition });
      set({ save_folder: data.save_folder });
      setFound(true);
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div>
      <h2 className="ttl" style={{ fontSize: 18 }}>Find Football Manager</h2>
      <p className="note" style={{ marginTop: 6 }}>FMCC finds FM and your save folder for you. In this browser preview it uses a sample save instead of your PC.</p>
      <div className="seg" style={{ marginTop: 16 }}>
        {["FM26", "FM27"].map((e) => <button key={e} className={form.edition === e ? "on" : ""} onClick={() => { set({ edition: e }); setFound(false); }} data-testid={`setup-edition-${e.toLowerCase()}`}>{e}</button>)}
      </div>
      {!found ? (
        <div style={{ marginTop: 18 }}><button className="btn btn-p btn-l" onClick={detect} disabled={busy} data-testid="setup-detect-button">{busy ? <Loader2 size={16} className="animate-spin" /> : <FolderSearch size={16} />}Find {form.edition}</button></div>
      ) : (
        <div style={{ marginTop: 18 }}>
          <div className="row" style={{ borderTop: 0, padding: 0 }}><span className="st ok" style={{ margin: 0 }} data-testid="setup-found-label">Found {form.edition} ✓</span><button className="btn" onClick={() => setEdit(!edit)} data-testid="setup-change-folder-button">Change</button></div>
          {edit ? <input className="inp" style={{ marginTop: 10 }} value={form.save_folder} onChange={(e) => set({ save_folder: e.target.value })} data-testid="setup-folder-input" />
            : <p className="note mono" style={{ marginTop: 10, wordBreak: "break-all" }} data-testid="setup-folder-path">{form.save_folder}</p>}
          <div style={{ marginTop: 18 }}><button className="btn btn-p btn-l" disabled={form.save_folder.trim().length < 3} onClick={next} data-testid="setup-next-1">Continue</button></div>
        </div>
      )}
    </div>
  );
};

const LaterStep = ({ title, text, next, id }) => (
  <div>
    <h2 className="ttl" style={{ fontSize: 18 }}>{title}</h2>
    <p className="note" style={{ marginTop: 6 }}>{text}</p>
    <div style={{ marginTop: 18 }}><button className="btn btn-l" onClick={next} data-testid={id}>Skip for now</button></div>
  </div>
);

const CareerStep = ({ form, set, next }) => (
  <div>
    <h2 className="ttl" style={{ fontSize: 18 }}>Name your career</h2>
    <p className="note" style={{ marginTop: 6 }}>Filled in from your latest save. You can change both.</p>
    <label className="lbl" style={{ marginTop: 16 }}>Club</label>
    <input className="inp" value={form.club_name} maxLength={60} onChange={(e) => set({ club_name: e.target.value })} data-testid="setup-club-input" />
    <label className="lbl" style={{ marginTop: 12 }}>Career name</label>
    <input className="inp" value={form.name} maxLength={60} onChange={(e) => set({ name: e.target.value })} data-testid="setup-career-input" />
    <div style={{ marginTop: 18 }}><button className="btn btn-p btn-l" disabled={!form.name.trim() || !form.club_name.trim()} onClick={next} data-testid="setup-next-3">Continue</button></div>
  </div>
);

const Health = ({ health, done }) => (
  <div data-testid="setup-health">
    <h2 className="ttl" style={{ fontSize: 18 }}>Health check</h2>
    {health.map((h) => (
      <div className="row" key={h.key} data-testid={`health-${h.key}`}>
        <span className={`st ${h.ok ? "ok" : "a"}`} style={{ margin: 0 }}>{h.ok ? "Ready" : "Later"}</span>
        <div><b>{h.label}</b><small>{h.detail}</small></div>
      </div>
    ))}
    <div style={{ marginTop: 18 }}><button className="btn btn-p btn-l" onClick={done} data-testid="setup-finish-button">Open FMCC</button></div>
  </div>
);

export default function Setup() {
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState(null);
  const [form, setForm] = useState({ edition: "FM27", save_folder: "", club_name: "Sample Club FC", name: "My first career" });
  const set = (p) => setForm((f) => ({ ...f, ...p }));
  const finish = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/setup/complete", form);
      setHealth(data.health);
      setStep(4);
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div className="setup grain" data-testid="setup-page">
      <div className="wiz">
        <img src="/fmcc-logo.png" alt="FMCC" style={{ height: 96, margin: "0 auto", display: "block" }} />
        <h1 className="h rise" style={{ textAlign: "center", fontSize: 38 }}>Welcome to <span className="serif">FMCC.</span></h1>
        <p className="lede" style={{ textAlign: "center" }}>Four quick steps and your club is ready.</p>
        <StepBar step={step} />
        <div className="card rise d1">
          {step === 0 && <FindStep form={form} set={set} next={() => setStep(1)} />}
          {step === 1 && <LaterStep id="setup-skip-analytics" next={() => setStep(2)} title="Install match analytics"
            text="The one-click FMMatchLens and BepInEx install arrives in stage 4. You can do it later from Settings." />}
          {step === 2 && <CareerStep form={form} set={set} next={() => setStep(3)} />}
          {step === 3 && <LaterStep id="setup-skip-key" next={finish} title="Add your OpenAI key (optional)"
            text={busy ? "Reading your save…" : "The DOF chat arrives in stage 4. You can add your key later in Settings."} />}
          {step === 4 && health && <Health health={health} done={() => qc.invalidateQueries()} />}
        </div>
      </div>
    </div>
  );
}
