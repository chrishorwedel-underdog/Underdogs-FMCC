import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { NAV } from "@/constants/nav";
import { GUIDES } from "@/constants/guides";

const STEPS = [...NAV.map((n) => ({ to: n.to, key: n.key, label: n.label })), { to: "/safety", key: "safety", label: "Project Safety" },
  { to: "/changes", key: "top-changes-button", label: "Game changes", what: "Every change FMCC makes in FM is recorded here, and you can undo it. Changes apply automatically unless you switch on Review changes before applying in Features." },
  { to: "/dof", key: "ask-dof", label: "Director of Football" }];

export const startTour = () => window.dispatchEvent(new Event("fmcc-tour"));

export const Tour = ({ ready }) => {
  const [i, setI] = useState(null);
  const nav = useNavigate();
  useEffect(() => {
    const go = () => setI(0);
    window.addEventListener("fmcc-tour", go);
    if (ready && !localStorage.getItem("fmcc-tour-done")) go();
    return () => window.removeEventListener("fmcc-tour", go);
  }, [ready]);
  useEffect(() => {
    if (i === null) { return undefined; }
    const s = STEPS[i];
    if (s) nav(s.to);
    const id = s?.key.startsWith("top-") ? s.key : `nav-${s?.key}`;
    const el = document.querySelector(`[data-testid="${id}"]`);
    el?.classList.add("tour-spot");
    return () => el?.classList.remove("tour-spot");
  }, [i, nav]);
  if (i === null) return null;
  const end = () => { localStorage.setItem("fmcc-tour-done", "1"); setI(null); nav("/"); };
  const done = i >= STEPS.length;
  const s = STEPS[i];
  return (
    <div className="tour-card" data-testid="tour-card">
      <div className="eyebrow">{done ? "All done" : `${i + 1} of ${STEPS.length}`}</div>
      <b data-testid="tour-title">{done ? "You're ready" : s.label}</b>
      <p data-testid="tour-text">{done ? "Replay this tour any time from Settings or the ? button at the top." : s.what || GUIDES[s.to]?.what}</p>
      <div style={{ display: "flex", gap: 8 }}>
        {!done && <button className="btn" onClick={end} data-testid="tour-skip">Skip tour</button>}
        <span style={{ marginLeft: "auto" }} />
        {i > 0 && !done && <button className="btn" onClick={() => setI(i - 1)} data-testid="tour-back">Back</button>}
        <button className="btn btn-p" onClick={() => (done ? end() : setI(i + 1))} data-testid="tour-next">{done ? "Finish" : "Next"}</button>
      </div>
    </div>
  );
};
