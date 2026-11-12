import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Info, ChevronDown, ChevronUp, Lightbulb, X, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { GUIDES } from "@/constants/guides";
import { api, errMsg } from "@/lib/api";

const TIPS = {
  "/": "Start with Up next: urgent things are at the top, each with one button.",
  "/scouting": "Type a name or pick a ready-made search. More filters are one click away.",
  "/squad": "Drag players on the pitch to swap them. Your lineup saves straight away.",
  "/dynamic-potential": "Reviews run in winter and at season end. Balance Preview shows what would change first.",
  "/club-analysis": "The first item in What to do first is the one to fix first.",
  "/reports": "Click any player in a report to open his profile.",
  "/changes": "Every batch can be undone here.",
  "/editor": "Club edits go into your save straight away, and the bell lists them.",
  "/punish": "Penalties apply to the save at once; anything for a new career waits until you start one.",
};
const read = (k) => JSON.parse(localStorage.getItem(k) || "{}");
const write = (k, v) => localStorage.setItem(k, JSON.stringify(v));

const Tip = ({ path }) => {
  const [seen, setSeen] = useState(() => read("fmcc-tips-seen"));
  if (!TIPS[path] || seen[path]) return null;
  const close = () => { const n = { ...seen, [path]: true }; write("fmcc-tips-seen", n); setSeen(n); };
  return (
    <div className="screen-tip rise" role="note" data-testid="screen-tip"><Lightbulb size={15} aria-hidden="true" /><span>{TIPS[path]}</span>
      <button className="ib" style={{ width: 26, height: 26, marginLeft: "auto" }} onClick={close} aria-label="Dismiss tip" data-testid="screen-tip-dismiss"><X size={13} /></button></div>
  );
};

export const NeedSave = ({ state }) => {
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const { pathname } = useLocation();
  if (!state?.career || state.career.next_save_no || ["/settings", "/appearance", "/connections", "/features", "/safety", "/downloads"].includes(pathname)) return null;
  const go = async () => { setBusy(true); try { const { data } = await api.post("/saves/read"); toast.success(`Read ${data.file_name}`); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); } };
  return (
    <div className="empty-st" style={{ marginBottom: 16 }} role="status" data-testid="need-save">
      <Info size={16} aria-hidden="true" /><div style={{ flex: 1 }}><b>Read a save first</b><p>This page fills in from your latest FM save. Save your game in FM, then read it.</p></div>
      <button className="btn btn-p" disabled={busy} onClick={go} data-testid="need-save-read"><RefreshCw size={13} className={busy ? "animate-spin" : ""} />Read my save</button>
    </div>
  );
};

export const ModuleGuide = () => {
  const { pathname } = useLocation();
  const g = GUIDES[pathname];
  const [hidden, setHidden] = useState(() => read("fmcc-guides-hidden"));
  const [visited, setVisited] = useState(() => read("fmcc-guides-visited"));
  const [firstHere, setFirstHere] = useState({});
  useEffect(() => {
    const v = read("fmcc-guides-visited");
    setFirstHere((f) => (pathname in f ? f : { ...f, [pathname]: !v[pathname] }));
    if (!v[pathname]) { const n = { ...v, [pathname]: true }; write("fmcc-guides-visited", n); setVisited(n); }
  }, [pathname]);
  if (!g) return <Tip path={pathname} />;
  const closed = pathname in hidden ? !!hidden[pathname] : !(firstHere[pathname] ?? !visited[pathname]);
  const toggle = () => {
    const next = { ...hidden, [pathname]: !closed };
    write("fmcc-guides-hidden", next);
    setHidden(next);
  };
  return (
    <>
      <div className="card guide rise" data-testid="module-guide">
        <button className="guide-head" onClick={toggle} aria-expanded={!closed} data-testid="module-guide-toggle">
          <Info size={15} /><b>What this page does</b><span className="sr-only" data-testid="module-guide-what">{g.what}</span><span style={{ color: "var(--dim)" }}>{closed ? "Show details" : "Hide details"}</span>
          {closed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
        </button>
        {!closed && (
          <div className="guide-body" data-testid="module-guide-body">
            <div><div className="eyebrow">On this page</div><ul>{g.features.map((f) => <li key={f}>{f}</li>)}</ul></div>
            <div><div className="eyebrow">How it works</div><ol>{g.how.map((h) => <li key={h}>{h}</li>)}</ol></div>
          </div>
        )}
      </div>
      <Tip path={pathname} />
    </>
  );
};
