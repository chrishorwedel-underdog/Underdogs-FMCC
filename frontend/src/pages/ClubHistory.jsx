import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { api, errMsg } from "@/lib/api";
import { useGet, PageHead, TabBar } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { Cabinet, SeasonTable, Timeline } from "@/components/history/Cabinet";
import { SeasonPage } from "@/components/history/SeasonPage";
import { Records, Leaders, Compare, HallOfFame } from "@/components/history/Records";

const TABS = [["cabinet", "Trophy Cabinet"], ["seasons", "Seasons"], ["records", "Records"], ["leaders", "Statistical Leaders"], ["compare", "Compare Seasons"], ["hall", "Hall of Fame"], ["timeline", "Timeline"]];

const PinForm = ({ seasons }) => {
  const qc = useQueryClient();
  const [t, setT] = useState("");
  const [pick, setS] = useState("");
  const s = pick || seasons[0] || "";
  const save = async () => { try { await api.post("/history/pins", { title: t, season: s }); setT(""); toast.success("Moment pinned"); qc.invalidateQueries({ queryKey: ["history-milestones"] }); } catch (e) { toast.error(errMsg(e)); } };
  return <div className="card" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }} data-testid="pin-form">
    <b>Pin a moment</b><input className="inp" style={{ flex: 1, minWidth: 200 }} value={t} maxLength={120} onChange={(e) => setT(e.target.value)} placeholder="e.g. Last-minute winner in the derby" data-testid="pin-title" />
    <select className="inp" style={{ width: "auto" }} value={s} onChange={(e) => setS(e.target.value)} data-testid="pin-season">{seasons.map((x) => <option key={x}>{x}</option>)}</select>
    <button className="btn btn-p" disabled={!t.trim() || !s} onClick={save} data-testid="pin-save">Pin</button></div>;
};

export default function ClubHistory() {
  const [params, setParams] = useSearchParams();
  const season = params.get("season");
  const tab = TABS.some(([k]) => k === params.get("tab")) ? params.get("tab") : "cabinet";
  const { data: list } = useGet("history-seasons", "/history/seasons");
  const { data: ms } = useGet("history-milestones", "/history/milestones", undefined, { enabled: tab === "timeline" });
  const seasons = (list?.seasons || []).map((s) => s.season);
  const go = (k) => setParams({ tab: k });
  return (
    <div data-testid="club-history-page">
      <PageHead eyebrow="Your club, season by season" title="Club History" purpose="Trophies, every season as it happened, club records and the moments that made them." />
      {season ? <SeasonPage season={season} /> : <>
        <div style={{ overflowX: "auto", marginBottom: 16 }}><TabBar id="history" value={tab} onChange={go} tabs={TABS} /></div>
        {tab === "cabinet" && <Cabinet />}
        {tab === "seasons" && (list ? <div className="card" style={{ padding: 8 }}><SeasonTable rows={list.seasons} /></div> : <Loading id="seasons-loading" rows={4} label="Loading seasons" />)}
        {tab === "records" && <Records />}
        {tab === "leaders" && <Leaders />}
        {tab === "compare" && (list ? <Compare seasons={seasons} /> : <Loading id="compare-loading" rows={3} label="Loading" />)}
        {tab === "hall" && <HallOfFame />}
        {tab === "timeline" && <div style={{ display: "grid", gap: 12 }}><PinForm seasons={seasons} /><div className="card">{ms ? <Timeline items={ms.milestones} full /> : <Loading id="timeline-loading" rows={4} label="Loading" />}</div></div>}
      </>}
    </div>
  );
}
