import { useQueryClient, useQuery } from "@tanstack/react-query";
import { HelpCircle, MoreHorizontal } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { startTour } from "@/components/Tour";
import { NotifyBell } from "@/components/Notify";
import { useRaw, setRaw } from "@/components/scout/ctx";
import { useNavigate } from "react-router-dom";
import { Search, RefreshCw, Settings, Wand2, Plug } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, ago, errMsg, gameDate } from "@/lib/api";

const linkTone = (iso) => {
  if (!iso) return "bad";
  return Date.now() - new Date(iso).getTime() > 6 * 3600 * 1000 ? "warn" : "ok";
};

export const TopBar = ({ career, onSearch, sample = true }) => {
  const qc = useQueryClient();
  const nav = useNavigate();
  const raw = useRaw();
  const [busy, setBusy] = useState(false);
  const { data: ch } = useQuery({ queryKey: ["changes"], queryFn: () => api.get("/changes").then((r) => r.data), refetchInterval: 5000 });
  const pending = ch?.queued?.length || 0;
  const { data: notes = [] } = useQuery({ queryKey: ["notices"], queryFn: () => api.get("/notices").then((r) => r.data), refetchInterval: 5000 });
  useEffect(() => {
    notes.forEach((n) => {
      api.post(`/notices/${n.id}/seen`);
      if (n.kind === "save_read") {
        toast.success(`New save read: ${gameDate(n.game_date, { day: "numeric", month: "long", year: "numeric" })} · ${n.players} players`, { id: n.id, duration: 12000, action: { label: "Check my save", onClick: () => nav(`/settings?section=safety&save=${n.save_no}`) } });
        qc.invalidateQueries();
      } else {
        toast.error(`FMCC couldn't read ${n.file_name}: ${n.message}`, { id: n.id, duration: 15000 });
      }
    });
  }, [notes]); // eslint-disable-line react-hooks/exhaustive-deps
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
        <div className="crest" data-testid="top-crest">{career?.club_name?.slice(0, 2).toUpperCase()}</div>
        <div><b data-testid="top-club-name">{career?.club_name}</b><span data-testid="top-game-date">{career?.edition} · {gameDate(career?.last_game_date)}</span></div>
      </div>
      <div className="srch" onClick={onSearch} data-testid="top-search-button"><Search size={15} />Search players, screens, actions…<kbd>Ctrl K</kbd></div>
      <div className="tr">
        <div className={`link ${tone}`} data-testid="game-link-pill" title={sample ? "Browser preview: reading a sample save" : "Open Connections"} onClick={() => nav("/settings?section=connections")} style={{ cursor: "pointer" }}>
          <span className="pulse" /><span className="lt">{sample ? "Sample save" : "Game linked"} · save read {ago(career?.last_read_at)}</span>
        </div>
        <button className="ib" onClick={readSave} disabled={busy} title="Read latest save" data-testid="read-save-button">
          <RefreshCw size={16} className={busy ? "animate-spin" : ""} />
        </button>
        <NotifyBell />
        <button className="ib" onClick={() => nav("/settings")} title="Settings" aria-label="Settings" data-testid="top-settings-button"><Settings size={16} /></button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild><button className="ib top-more" style={{ position: "relative" }} title="More" aria-label="More" data-testid="top-more-button"><MoreHorizontal size={16} />{pending > 0 && <span className="more-count mono" data-testid="top-changes-count">{pending}</span>}</button></DropdownMenuTrigger>
          <DropdownMenuContent align="end" data-testid="top-more-menu">
            <DropdownMenuItem onClick={() => nav("/changes")} data-testid="top-more-changes"><Wand2 size={14} />Game changes{pending ? ` (${pending} waiting)` : ""}</DropdownMenuItem>
            <DropdownMenuItem onClick={() => setRaw(!raw)} data-testid="top-more-raw">{raw ? "Show percentiles instead of raw numbers" : "Show raw numbers instead of percentiles"}</DropdownMenuItem>
            <DropdownMenuItem onClick={() => nav("/settings?section=connections")} data-testid="top-more-connections"><Plug size={14} />Connections</DropdownMenuItem>
            <DropdownMenuItem onClick={startTour} data-testid="top-more-tour"><HelpCircle size={14} />Help: take the tour</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};
