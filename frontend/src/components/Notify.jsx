import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bell, AlertTriangle } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const PAGE_OF = { "/reports": ["reports"], "/development": ["development"], "/dynamic-potential": ["dp"], "/elite-training": ["elite"], "/breakout": ["breakout"], "/squad": ["squad"], "/scouting": ["window"] };

const Ring = ({ p }) => (
  <svg width="18" height="18" viewBox="0 0 36 36" style={{ flexShrink: 0 }}><circle cx="18" cy="18" r="15" fill="none" stroke="var(--s3)" strokeWidth="5" />
    <circle cx="18" cy="18" r="15" fill="none" stroke="var(--acc)" strokeWidth="5" strokeDasharray={`${(p / 100) * 94} 94`} transform="rotate(-90 18 18)" /></svg>
);

const Chip = ({ c }) => {
  const nav = useNavigate();
  return (
    <button className="hchip" onClick={() => nav(c.link)} title={`${c.date}${c.estimated ? " · estimated from the league's usual dates" : ""}`} data-testid={`countdown-${c.key}`}>
      <Ring p={c.progress} /><span>{c.text}{c.estimated && <small style={{ color: "var(--dim)" }}> · est.</small>}</span>
    </button>
  );
};

const Missed = ({ m, act }) => (
  <div className="chk warn" style={{ padding: "10px 12px" }} data-testid={`missed-${m.key}`}>
    <span className="chk-i"><AlertTriangle size={15} /></span>
    <div style={{ flex: 1 }}><b>{m.text}</b>{m.handled ? <small>{m.handled.label}</small> : <small>You can make it late from save #{m.nearest_save} ({m.nearest_date}); it will be labelled as late.</small>}</div>
    {!m.handled && <><button className="btn" onClick={() => act(() => api.post(`/notify/missed/${m.key}`, { action: "late" }), (r) => r.label, ["countdowns", "notices"])} data-testid={`missed-late-${m.key}`}>Make it late</button>
      <button className="btn" onClick={() => act(() => api.post(`/notify/missed/${m.key}`, { action: "dismiss" }), "Dismissed", ["countdowns", "notices"])} data-testid={`missed-dismiss-${m.key}`}>Dismiss</button></>}
  </div>
);

export const UpNext = () => {
  const { data } = useGet("countdowns", "/notify/countdowns");
  const act = useAct();
  if (!data?.items.length) return null;
  return (
    <div style={{ marginBottom: 22 }} data-testid="up-next">
      <div className="eyebrow">Up next in your save</div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>{data.items.slice(0, 6).map((c) => <Chip key={c.key} c={c} />)}</div>
      {data.missed.filter((m) => !m.handled).slice(0, 3).map((m) => <div key={m.key} style={{ marginTop: 8 }}><Missed m={m} act={act} /></div>)}
    </div>
  );
};

export const PageCountdown = () => {
  const { pathname } = useLocation();
  const keys = PAGE_OF[pathname];
  const { data } = useGet("countdowns", "/notify/countdowns", undefined, { enabled: !!keys });
  const act = useAct();
  if (!keys || !data) return null;
  const items = data.items.filter((c) => keys.includes(c.page));
  const miss = pathname === "/reports" ? data.missed : [];
  if (!items.length && !miss.length) return null;
  return (
    <div style={{ display: "grid", gap: 8, marginBottom: 16 }} data-testid="page-countdown">
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>{items.slice(0, 8).map((c) => <Chip key={c.key} c={c} />)}</div>
      {miss.map((m) => <Missed key={m.key} m={m} act={act} />)}
    </div>
  );
};

const groupOf = (n, latest) => (n.at.slice(0, 10) === new Date().toISOString().slice(0, 10) ? "Today" : latest && n.game_date?.slice(0, 7) === latest.slice(0, 7) ? "This month in-game" : "Earlier");

export const useNotices = () => useGet("notices", "/notify", undefined, { refetchInterval: 60000 });

export const NotifyBell = () => {
  const { data } = useNotices();
  const act = useAct();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const latest = data?.items.map((n) => n.game_date).sort().pop();
  const go = (n) => { setOpen(false); api.post(`/notify/${n.id}/read`).finally(() => act(async () => ({ data: {} }), null, ["notices"])); nav(n.link); };
  return (
    <div style={{ position: "relative" }}>
      <button className="ib" onClick={() => setOpen(!open)} title="Notifications" data-testid="notify-bell"><Bell size={16} />
        {!!data?.unread && <span className="bell-n" data-testid="notify-count">{data.unread}</span>}</button>
      {open && <div style={{ position: "fixed", inset: 0, zIndex: 79 }} onClick={() => setOpen(false)} data-testid="notify-backdrop" />}
      {open && <div className="bell-pop card" data-testid="notify-panel">
        <div className="ttl">Notifications<span style={{ marginLeft: "auto" }} />
          <button className="btn" onClick={() => act(() => api.post("/notify/read-all"), null, ["notices"])} data-testid="notify-read-all">Mark all read</button>
          <button className="btn" onClick={() => act(() => api.post("/notify/clear"), "Cleared (kept in history)", ["notices"])} data-testid="notify-clear">Clear</button></div>
        {!data?.items.length && <p className="note">Nothing new.</p>}
        {["Today", "This month in-game", "Earlier"].map((g) => { const rows = (data?.items || []).filter((n) => groupOf(n, latest) === g); return rows.length ? <div key={g}><div className="eyebrow" style={{ marginTop: 8 }}>{g}</div>
          {rows.map((n) => <div key={n.id} className={`row bell-row${n.read ? "" : " unread"}`} onClick={() => go(n)} data-testid={`notice-${n.id}`}><div style={{ flex: 1 }}><b>{n.title}</b><small>{n.text}</small></div></div>)}</div> : null; })}
      </div>}
    </div>
  );
};

export const NotifySettings = () => {
  const { data } = useGet("notify-prefs", "/notify/prefs");
  const act = useAct();
  if (!data) return null;
  return (
    <div className="card rise d5" data-testid="notify-settings">
      <div className="ttl">Notifications</div><p className="note" style={{ marginTop: 4 }}>Inside FMCC only. Switching one off hides it; nothing is deleted.</p>
      {Object.entries(data.labels).map(([k, l]) => <div key={k} className="row"><span style={{ flex: 1 }}>{l}</span>
        <Switch checked={data.prefs[k]} onCheckedChange={(v) => act(() => api.put("/notify/prefs", { [k]: v }), null, ["notify-prefs", "notices"])} data-testid={`notify-pref-${k}`} /></div>)}
    </div>
  );
};
