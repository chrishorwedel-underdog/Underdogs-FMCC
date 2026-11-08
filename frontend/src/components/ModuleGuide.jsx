import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Info, ChevronDown, ChevronUp } from "lucide-react";
import { GUIDES } from "@/constants/guides";

export const ModuleGuide = () => {
  const { pathname } = useLocation();
  const g = GUIDES[pathname];
  const [hidden, setHidden] = useState(() => JSON.parse(localStorage.getItem("fmcc-guides-hidden") || "{}"));
  if (!g) return null;
  const closed = !!hidden[pathname];
  const toggle = () => {
    const next = { ...hidden, [pathname]: !closed };
    localStorage.setItem("fmcc-guides-hidden", JSON.stringify(next));
    setHidden(next);
  };
  return (
    <div className="card guide rise" data-testid="module-guide">
      <button className="guide-head" onClick={toggle} data-testid="module-guide-toggle">
        <Info size={15} /><b>What this page does</b><span data-testid="module-guide-what">{g.what}</span>
        {closed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
      </button>
      {!closed && (
        <div className="guide-body" data-testid="module-guide-body">
          <div><div className="eyebrow">On this page</div><ul>{g.features.map((f) => <li key={f}>{f}</li>)}</ul></div>
          <div><div className="eyebrow">How it works</div><ol>{g.how.map((h) => <li key={h}>{h}</li>)}</ol></div>
        </div>
      )}
    </div>
  );
};
