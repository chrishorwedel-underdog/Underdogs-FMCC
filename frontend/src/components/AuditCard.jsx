import { useGet } from "@/lib/ui";
import { ago } from "@/lib/api";

export const AuditCard = ({ title = "Game-change record" }) => {
  const { data = [] } = useGet("audit", "/audit", undefined, { refetchInterval: 3000 });
  return (
    <div className="card" data-testid="audit-trail"><div className="ttl">{title}</div>
      <p className="note" style={{ marginTop: 4 }}>Every entry is added, never edited or removed.</p>
      <div style={{ maxHeight: 420, overflowY: "auto" }}>
        {data.map((a) => <div className="row" key={a.id}><div style={{ flex: 1 }}><b style={{ textTransform: "capitalize" }}>{a.action}</b>{a.player_name ? ` · ${a.player_name}` : ""}<small>{a.detail} · {a.source}</small></div><small>{ago(a.at)}</small></div>)}
        {!data.length && <p className="note" style={{ marginTop: 8 }}>Nothing recorded yet.</p>}
      </div>
    </div>
  );
};
