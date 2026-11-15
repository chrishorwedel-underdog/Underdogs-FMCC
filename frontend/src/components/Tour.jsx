import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { NAV } from "@/constants/nav";
import { GUIDES } from "@/constants/guides";

const STEPS = [{ to: "/", key: "home", label: "Welcome to FMCC", what: "This is Home: your club at a glance. Press Next for a quick look round every screen, or Skip tour to start straight away." },
  ...NAV.map((n) => ({ to: n.to, key: n.key, label: n.label })), { to: "/settings?section=safety", key: "safety", label: "Project Safety" },
  { to: "/changes", key: "top-more-button", label: "Game changes", what: "Every change FMCC makes in FM is recorded in Game changes (in the More menu), and you can undo it. Changes apply automatically unless you switch on Review changes before applying in Settings, Features." },
  { to: "/dof", key: "ask-dof", label: "Director of Football" }];

// Short guided tour for a new career: the screens that matter in the first week.
const FIRST = [
  { to: "/", key: "home", label: "Welcome to your new career", what: "Home is your club at a glance: what's urgent, highlights and what changed since your last save. Press Next for a two-minute look round, or Skip tour." },
  { to: "/settings?section=career", key: "top-settings-button", label: "What the game calls you", what: "Set the name FMCC uses for you and pick your look. Everything here is saved for this career only." },
  { to: "/squad", key: "squad", label: "Squad", what: "Your players, best lineup, depth chart and tactic fit. Switch to Players for a table or cards with filters." },
  { to: "/development", key: "development", label: "Youth Development", what: "Give youngsters a minutes target and a goal (small, steady or big improvement). FMCC tracks progress in plain words." },
  { to: "/scouting", key: "scouting", label: "Scout Players", what: "Search every player FMCC can see, compare up to four, and watch players to get alerts." },
  { to: "/club-history", key: "club-history", label: "Club History", what: "Your trophies, seasons, records and Hall of Fame build up automatically as you play." },
  { to: "/changes", key: "top-more-button", label: "Game changes", what: "Every change FMCC makes in FM is listed here and can be undone. Changes apply automatically unless you switch on Review changes in Settings." },
  { to: "/dof", key: "ask-dof", label: "Director of Football", what: "Ask your Director of Football anything about your club. He answers from your save." }];

export const startTour = (mode = "full") => window.dispatchEvent(new CustomEvent("fmcc-tour", { detail: mode }));
export const markNewCareer = () => localStorage.setItem("fmcc-tour-new-career", "1");

export const Tour = ({ ready }) => {
  const [i, setI] = useState(null);
  const [steps, setSteps] = useState(FIRST);
  const nav = useNavigate();
  const { pathname } = useLocation();
  useEffect(() => {
    const go = (e) => { setSteps(e?.detail === "first" ? FIRST : STEPS); setI(0); };
    window.addEventListener("fmcc-tour", go);
    const fresh = localStorage.getItem("fmcc-tour-new-career") || !localStorage.getItem("fmcc-tour-done");
    if (ready && fresh) { if (pathname !== "/") nav("/"); go({ detail: "first" }); }
    return () => window.removeEventListener("fmcc-tour", go);
  }, [ready]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (i === null) { return undefined; }
    const s = steps[i];
    if (s) nav(s.to);
    const id = s?.key.startsWith("top-") ? s.key : `nav-${s?.key}`;
    const el = document.querySelector(`[data-testid="${id}"]`);
    el?.classList.add("tour-spot");
    return () => el?.classList.remove("tour-spot");
  }, [i, nav, steps]);
  if (i === null) return null;
  const end = () => { localStorage.setItem("fmcc-tour-done", "1"); localStorage.removeItem("fmcc-tour-new-career"); setI(null); };
  const done = i >= steps.length;
  const s = steps[i];
  return (
    <div className="tour-card" data-testid="tour-card">
      <div className="eyebrow">{done ? "All done" : `${i + 1} of ${steps.length}`}</div>
      <b data-testid="tour-title">{done ? "You're ready" : s.label}</b>
      <p data-testid="tour-text">{done ? "Replay this tour, or the full tour of every screen, any time from Settings or the More menu." : s.what || GUIDES[s.to]?.what}</p>
      <div style={{ display: "flex", gap: 8 }}>
        {!done && <button className="btn" onClick={end} data-testid="tour-skip">Skip tour</button>}
        <span style={{ marginLeft: "auto" }} />
        {i > 0 && !done && <button className="btn" onClick={() => setI(i - 1)} data-testid="tour-back">Back</button>}
        <button className="btn btn-p" onClick={() => (done ? end() : setI(i + 1))} data-testid="tour-next">{done ? "Finish" : "Next"}</button>
      </div>
    </div>
  );
};
