import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FileCheck2 } from "lucide-react";
import { useGet, PageHead } from "@/lib/ui";
import { ago, gameDate } from "@/lib/api";
import { BackupsCard } from "@/components/BackupsCard";
import { AuditCard } from "@/components/AuditCard";

const List = ({ title, items, id }) => (
  <div style={{ marginTop: 10 }} data-testid={`check-${id}`}>
    <div className="eyebrow">{title} · {items.length}</div>
    <p className="note" style={{ marginTop: 4 }}>{items.length ? items.slice(0, 12).join(", ") + (items.length > 12 ? ` and ${items.length - 12} more` : "") : "None"}</p>
  </div>
);

const SaveCheck = () => {
  const [params] = useSearchParams();
  const { data: saves = [] } = useGet("saves", "/saves");
  const [no, setNo] = useState(params.get("save"));
  useEffect(() => { if (no == null && saves.length) setNo(String(saves[0].save_no)); }, [saves, no]);
  const { data: r } = useGet("save-check", `/saves/${no}/check`, { no }, { enabled: no != null });
  return (
    <div className="card rise d2" data-testid="save-check-card">
      <div className="ttl"><FileCheck2 size={15} />Check my save<span style={{ marginLeft: "auto" }} />
        <select className="inp" style={{ width: 260, height: 34 }} value={no ?? ""} onChange={(e) => setNo(e.target.value)} data-testid="save-check-select">
          {saves.map((s) => <option key={s.save_no} value={s.save_no}>{s.file_name} · {gameDate(s.game_date, { day: "numeric", month: "short", year: "numeric" })}</option>)}
        </select></div>
      {r && <>
        <p className="sent" style={{ marginTop: 10 }} data-testid="save-check-summary">Read <b>{r.players}</b> players at <b>{r.club_name}</b> from <span className="mono">{r.file_name}</span>, in-game date <b>{gameDate(r.game_date, { day: "numeric", month: "long", year: "numeric" })}</b>, {ago(r.read_at)} by {r.reader}.</p>
        {!r.first && <p className="note" style={{ marginTop: 6 }}>{r.same_ids} players matched the previous save by their game ID, never by name.</p>}
        <div style={{ marginTop: 10 }} data-testid="save-check-gaps">{Object.keys(r.gaps).length
          ? Object.entries(r.gaps).map(([k, v]) => <span key={k} className="st a" style={{ marginRight: 6 }}>{v} without {k}</span>)
          : <span className="st ok">Every field was read</span>}</div>
        {!r.first && <><List id="new" title="New players" items={r.new_players} /><List id="left" title="Left the squad" items={r.left} /><List id="renamed" title="Same ID, new name" items={r.renamed} /></>}
      </>}
      {!saves.length && <p className="note" style={{ marginTop: 8 }}>No saves read yet.</p>}
    </div>
  );
};

export default function Safety() {
  return (
    <div data-testid="safety-page">
      <PageHead eyebrow="Backups, save checks and the game-change record" title="Project Safety" />
      <div className="homegrid">
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><SaveCheck /><AuditCard /></div>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><BackupsCard /></div>
      </div>
    </div>
  );
}
