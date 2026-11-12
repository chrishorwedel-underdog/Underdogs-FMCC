import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const RANK = { urgent: 0, soon: 1, later: 2 };
const TAG = { urgent: "Urgent", soon: "Soon", later: "Later" };
const OPEN = { reports: "Open reports", development: "Open Development", dp: "Open Dynamic Potential", elite: "Open Elite Training", breakout: "Open Breakout Player", window: "Open Scout Players", squad: "Open Squad" };

const build = (attention, cd) => {
  const out = [];
  (cd?.missed || []).filter((m) => !m.handled).forEach((m) => out.push({ id: `missed-${m.key}`, level: "urgent", text: m.text, sub: `You can still make it late from save #${m.nearest_save}; it will be labelled as late.`, missed: m }));
  attention.forEach((a) => out.push({ id: `att-${a.kind}-${a.unique_id}`, level: a.kind === "minutes" ? "urgent" : "soon", text: a.text, sub: a.sub, link: `/squad?player=${a.unique_id}`, label: "View player" }));
  (cd?.items || []).forEach((c) => out.push({ id: `cd-${c.key}`, level: c.days <= 7 ? "urgent" : c.days <= 31 ? "soon" : "later", text: c.text, sub: `${c.date}${c.estimated ? " · estimated from the league's usual dates" : ""}`, link: c.link, label: OPEN[c.page] || "Open", days: c.days }));
  return out.sort((a, b) => RANK[a.level] - RANK[b.level] || (a.days ?? -1) - (b.days ?? -1));
};

export const UpNextPanel = ({ attention }) => {
  const { data: cd } = useGet("countdowns", "/notify/countdowns");
  const act = useAct();
  const nav = useNavigate();
  const items = build(attention, cd).slice(0, 10);
  const urgent = items.filter((i) => i.level === "urgent").length;
  return (
    <section className="upnext rise d2" aria-label="Up next in your save" data-testid="home-up-next">
      <div className="ttl" style={{ marginBottom: 6 }}>Up next in your save
        {urgent > 0 && <span className="st r" style={{ marginLeft: 10 }} data-testid="up-next-urgent-count">{urgent} urgent</span>}</div>
      {!items.length && <p className="note" data-testid="up-next-empty">All clear. Nothing needs you right now.</p>}
      {items.map((it, i) => (
        <div className="un-row" key={it.id} data-testid={`up-next-item-${i}`}>
          <span className={`un-tag ${it.level}`} data-testid={`up-next-level-${i}`}>{TAG[it.level]}</span>
          <div style={{ flex: 1, minWidth: 0 }}><p>{it.text}</p><small>{it.sub}</small></div>
          {it.missed
            ? <button className="btn btn-p" onClick={() => act(() => api.post(`/notify/missed/${it.missed.key}`, { action: "late" }), (r) => r.label, ["countdowns", "notices", "home"])} data-testid={`up-next-action-${i}`}>Make it late</button>
            : <button className="btn" onClick={() => nav(it.link)} data-testid={`up-next-action-${i}`}>{it.label}</button>}
        </div>
      ))}
    </section>
  );
};
