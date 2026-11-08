import { useQueryClient, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Search, RefreshCw, Settings, Wand2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { api, ago, errMsg, gameDate } from "@/lib/api";

const linkTone = (iso) => {
  if (!iso) return "bad";
  return Date.now() - new Date(iso).getTime() > 6 * 3600 * 1000 ? "warn" : "ok";
};

export const TopBar = ({ career, onSearch }) => {
  const qc = useQueryClient();
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const { data: ch } = useQuery({ queryKey: ["changes"], queryFn: () => api.get("/changes").then((r) => r.data), refetchInterval: 5000 });
  const pending = ch?.queued?.length || 0;
  const readSave = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/saves/read");
      toast.success(`Read ${data.file_name}: ${data.players} players`);
      qc.invalidateQueries();
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setBusy(false);
    }
  };
  const tone = linkTone(career?.last_read_at);
  return (
    <header className="top" data-testid="top-bar">
      <div className="club">
        <div className="crest">{career?.club_name?.slice(0, 2).toUpperCase()}</div>
        <div><b data-testid="top-club-name">{career?.club_name}</b><span data-testid="top-game-date">{career?.edition} · {gameDate(career?.last_game_date)}</span></div>
      </div>
      <div className="srch" onClick={onSearch} data-testid="top-search-button"><Search size={15} />Search players, screens, actions…<kbd>Ctrl K</kbd></div>
      <div className="tr">
        <div className={`link ${tone}`} data-testid="game-link-pill" title="Browser preview: reading a sample save">
          <span className="pulse" /><span className="lt">Sample save · read {ago(career?.last_read_at)}</span>
        </div>
        <button className="ib" onClick={readSave} disabled={busy} title="Read latest save" data-testid="read-save-button">
          <RefreshCw size={16} className={busy ? "animate-spin" : ""} />
        </button>
        <button className="ib" style={{ position: "relative", width: "auto", padding: "0 10px", gap: 6, display: "flex" }} onClick={() => nav("/changes")} title="Game changes" data-testid="top-changes-button">
          <Wand2 size={16} /><span style={{ fontSize: 12.5 }}>Game changes</span>{pending > 0 && <span className="st a mono" style={{ margin: 0 }} data-testid="top-changes-count">{pending}</span>}
        </button>
        <button className="ib" onClick={() => nav("/settings")} title="Settings" data-testid="top-settings-button"><Settings size={16} /></button>
      </div>
    </header>
  );
};
