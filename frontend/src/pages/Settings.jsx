import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { api, ago, gameDate, errMsg } from "@/lib/api";
import { CareersCard } from "@/components/CareersCard";
import { AddressCard } from "@/components/AddressPick";
import { UpdatesCard } from "@/components/UpdatesCard";
import { BackupsCard } from "@/components/BackupsCard";
import { startTour } from "@/components/Tour";
import { TestingCard } from "@/components/TestingCard";
import { NotifySettings } from "@/components/Notify";

const CREDITS = [["fmsave", "MIT", "Save reader"], ["FMLibreEditor", "GPL-3.0", "Game editor · its command-line tool is built into FMCC · source: github.com/tozmoz/FMLibreEditor"], ["FMMatchLens", "MIT", "Match analytics"],
  ["BepInEx", "LGPL-2.1", "Add-on loader"], ["FM Player Analyzer", "GPL-3.0", "Ideas for role ratings and registration checks"],
  ["ScoutSheet", "MIT", "Scouting views, fair price, Deal Finder and Offers, rebuilt inside Scout Players"], ["FMDataLab", "No code used", "Its analytics ideas and published possession method, rebuilt"],
  ["Global League Strength and Player Model", "Your workbook", "League strength (408 rated competitions, Opta snapshot 6 Nov 2026), position weights, grades and similarity"],
  ["FMST26", "No code used", "Inspiration for formulas and advanced filters"], ["fmOS", "No code used", "Inspiration for the quadrant chart, replacement search and price explained"],
  ["FM Dossier", "No code used", "Inspiration for tactic fit, squad gaps and the shape advisor"], ["sortitoutsi Punish Manchester City", "No code used", "Inspiration for Punish a Club"], ["Recruitment Lab screenshots", "No code or images used", "Inspiration for Explore, Shortlist board, Compare, the player profile and DOF picks"]];

const SavesCard = () => {
  const { data = [] } = useQuery({ queryKey: ["saves"], queryFn: () => api.get("/saves").then((r) => r.data) });
  return (
    <div className="card rise d4" data-testid="saves-card">
      <div className="ttl">Saves read</div>
      <div style={{ marginTop: 6, maxHeight: 280, overflowY: "auto" }}>
        {data.map((s) => (
          <div className="row" key={s.id} data-testid={`save-row-${s.save_no}`}>
            <div style={{ flex: 1 }}><span className="mono" style={{ fontSize: 12.5 }}>{s.file_name}</span><small>Game date {gameDate(s.game_date, { day: "numeric", month: "short", year: "numeric" })} · {s.reader}</small></div>
            <small>{ago(s.read_at)}</small>
          </div>
        ))}
      </div>
    </div>
  );
};

const AutoReadCard = ({ on, sample }) => {
  const qc = useQueryClient();
  const set = async (v) => {
    try { await api.put("/settings/auto-read", { auto_read: v }); qc.invalidateQueries({ queryKey: ["state"] }); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="card rise d4" data-testid="auto-read-card">
      <div className="row" style={{ borderTop: 0 }}><div style={{ flex: 1 }}><b>Read new saves automatically</b><small>{sample ? "Windows program: while FMCC is open, each new save is read once FM finishes writing it. Here, use the refresh button." : "While FMCC is open, each new save is read once FM finishes writing it. The refresh button still works."}</small></div>
        <Switch checked={on} onCheckedChange={set} data-testid="auto-read-switch" /></div>
    </div>
  );
};

const KeyCard = () => {
  const [key, setKey] = useState("");
  const save = async () => {
    try { await api.put("/dof/key", { key }); setKey(""); toast.success("OpenAI key saved on this PC"); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="card rise d5" data-testid="openai-key-card">
      <div className="ttl">DOF chat key</div>
      <p className="note" style={{ marginTop: 6 }}>Your own OpenAI key. It is stored only on this PC and never shown again.</p>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}><input className="inp mono" type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder="sk-..." data-testid="openai-key-input" />
        <button className="btn btn-p" style={{ height: 40 }} disabled={key.length < 20} onClick={save} data-testid="openai-key-save">Save</button></div>
    </div>
  );
};

export default function Settings({ state }) {
  return (
    <div data-testid="settings-page">
      <div className="head rise"><div><div className="eyebrow">Careers, updates and backups</div><h1 className="h">Settings</h1></div></div>
      {state.sample_mode && <div className="banner rise" style={{ marginBottom: 20 }} data-testid="sample-mode-banner">
        <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>Browser preview: FMCC is reading a built-in sample save, not your PC. Each refresh in the top bar reads the next month of that sample. The real fmsave reader is packaged in the Windows program.</span>
      </div>}
      <div style={{ marginBottom: 20 }}><TestingCard /></div>
      <div className="sgrid">
        <div style={{ display: "grid", gap: 20, alignContent: "start" }}><CareersCard career={state.career} key={state.career.id} /><AddressCard current={state.address} key={state.address} /><AutoReadCard on={state.auto_read_saves !== false} sample={state.sample_mode} /><SavesCard /></div>
        <div style={{ display: "grid", gap: 20, alignContent: "start" }}>
          <UpdatesCard autoInstall={state.auto_install_updates} />
          <BackupsCard />
          {!state.sample_mode && <KeyCard />}
          <NotifySettings />
          <div className="card rise d5" data-testid="tour-settings-card"><div className="ttl">Guided tour</div><p className="note" style={{ marginTop: 4 }}>A click-through of every page. Replaying it never changes any data.</p><button className="btn btn-p" style={{ marginTop: 8 }} onClick={startTour} data-testid="settings-take-tour">Take the tour</button></div>
          <div className="card rise d5" data-testid="credits-card">
            <div className="ttl">Credits</div>
            {CREDITS.map(([n, l, r]) => <div className="row" key={n}><div style={{ flex: 1 }}>{n}<small>{r}</small></div><span className="st n">{l}</span></div>)}
            <p className="note" style={{ marginTop: 8 }}>FMCC is released as open source under GPL-3.0. Last update check {ago(state.last_update_check)}.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
