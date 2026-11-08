import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { api, ago, gameDate } from "@/lib/api";
import { CareersCard } from "@/components/CareersCard";
import { UpdatesCard } from "@/components/UpdatesCard";
import { BackupsCard } from "@/components/BackupsCard";

const CREDITS = [["fmsave", "MIT", "Save reader"], ["FMLibreEditor", "GPL-3.0", "Game editor"], ["FMMatchLens", "MIT", "Match analytics"],
  ["BepInEx", "LGPL-2.1", "Add-on loader"], ["FM Player Analyzer", "GPL-3.0", "Ideas for role ratings and registration checks"]];

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

export default function Settings({ state }) {
  return (
    <div data-testid="settings-page">
      <div className="head rise"><div><div className="eyebrow">Careers, updates and backups</div><h1 className="h">Settings</h1></div></div>
      <div className="banner rise" style={{ marginBottom: 20 }} data-testid="sample-mode-banner">
        <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>Browser preview: FMCC is reading a built-in sample save, not your PC. Each refresh in the top bar reads the next month of that sample. The real fmsave reader is packaged in the Windows program.</span>
      </div>
      <div className="sgrid">
        <div style={{ display: "grid", gap: 20, alignContent: "start" }}><CareersCard career={state.career} key={state.career.id} /><SavesCard /></div>
        <div style={{ display: "grid", gap: 20, alignContent: "start" }}>
          <UpdatesCard autoInstall={state.auto_install_updates} />
          <BackupsCard />
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
