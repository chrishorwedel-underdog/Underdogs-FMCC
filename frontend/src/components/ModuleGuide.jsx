import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Info, ChevronUp, Lightbulb, X, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { GUIDES, SIMPLE } from "@/constants/guides";
import { api, errMsg } from "@/lib/api";
import { usePersist, useCareerId, readPersist } from "@/lib/remember";
import { Switch } from "@/components/ui/switch";

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

// Each screen tip shows during one visit only, then never again.
const Tip = ({ path }) => {
  const [seen, setSeen] = useState(() => read("fmcc-tips-seen"));
  useEffect(() => { if (TIPS[path] && !read("fmcc-tips-seen")[path]) { write("fmcc-tips-seen", { ...read("fmcc-tips-seen"), [path]: true }); } }, [path]);
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

export const useGuidePrefs = () => {
  const [on, setOn] = usePersist("guides-on", true);
  const [closed, setClosed] = usePersist("guides-closed", {});
  const [open, setOpen] = usePersist("guides-open", {});
  return { on, closed, open, toggle: (p, v) => setOpen((o) => ({ ...o, [p]: v })), close: (p) => setClosed((c) => ({ ...c, [p]: true })), setOn: (v) => { setOn(v); if (v) { setClosed({}); } } };
};

// Small "How this page works" link shown beside each page title.
export const GuideLink = () => {
  const { pathname } = useLocation();
  const g = useGuidePrefs();
  if (!GUIDES[pathname] || !g.on || g.closed[pathname]) return null;
  const isOpen = !!g.open[pathname];
  return <button className="guide-link" onClick={() => g.toggle(pathname, !isOpen)} aria-expanded={isOpen} data-testid="guide-link"><Info size={13} />{isOpen ? "Hide how this page works" : "How this page works"}</button>;
};

export const GuidesCard = () => {
  const g = useGuidePrefs();
  return (
    <div className="card rise d5" data-testid="guides-settings-card">
      <div className="ttl" style={{ display: "flex", alignItems: "center", gap: 10 }}>Show 'What this page does' boxes
        <Switch style={{ marginLeft: "auto" }} checked={g.on} onCheckedChange={g.setOn} data-testid="guides-show-switch" /></div>
      <p className="note" style={{ marginTop: 4 }}>Turning this on brings back every box you closed. Saved for this career.</p>
    </div>
  );
};

export const ModuleGuide = () => {
  const { pathname } = useLocation();
  const g = GUIDES[pathname];
  const prefs = useGuidePrefs();
  const [visited, setVisited] = usePersist("guides-visited", {});
  const cid = useCareerId();
  const prev = useRef(null);
  useEffect(() => {
    if (prev.current && prev.current !== pathname && prefs.open[prev.current]) { prefs.toggle(prev.current, false); }
    prev.current = pathname;
    if (!cid || !g) { return; }
    if (readPersist(cid, "guides-visited", {})[pathname]) { if (readPersist(cid, "guides-open", {})[pathname]) { prefs.toggle(pathname, false); } return; }
    setVisited((v) => ({ ...v, [pathname]: true }));
    prefs.toggle(pathname, true);
  }, [pathname, cid]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!g || !prefs.on || prefs.closed[pathname] || !prefs.open[pathname]) return cid && (!g || readPersist(cid, "guides-visited", {})[pathname]) ? <Tip key={pathname} path={pathname} /> : null;
  return (
    <>
      <div className="card guide rise" data-testid="module-guide">
        <div style={{ display: "flex", alignItems: "center" }}>
        <button className="guide-head" onClick={() => prefs.toggle(pathname, false)} aria-expanded data-testid="module-guide-toggle">
          <Info size={15} /><b>How this page works</b><span className="sr-only" data-testid="module-guide-what">{g.what}</span><span style={{ color: "var(--dim)" }}>Hide</span>
          <ChevronUp size={15} />
        </button>
        <button className="ib guide-x" onClick={() => prefs.close(pathname)} aria-label="Close this box on this screen" title="Close this box on this screen. Bring it back in Settings." data-testid="module-guide-close"><X size={14} /></button>
        </div>
        <div className="guide-body" data-testid="module-guide-body">
          <div className="guide-simple" data-testid="module-guide-simple"><div className="eyebrow">What this feature does</div><p>{SIMPLE[pathname] || g.what}</p></div>
          <div><div className="eyebrow">On this page</div><ul>{g.features.map((f) => <li key={f}>{f}</li>)}</ul></div>
          <div><div className="eyebrow">How it works</div><ol>{g.how.map((h) => <li key={h}>{h}</li>)}</ol></div>
        </div>
      </div>
    </>
  );
};
