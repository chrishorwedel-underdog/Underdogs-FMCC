import { Hourglass } from "lucide-react";
import { STAGE_TEXT, NAV } from "@/constants/nav";

export const ComingSoon = ({ k }) => {
  const n = NAV.find((x) => x.key === k) || { label: "Ask your DOF", stage: 4, c: "#E5302F" };
  return (
    <div data-testid={`coming-soon-${k}`}>
      <div className="eyebrow rise">Arrives in stage {n.stage}</div>
      <h1 className="h rise d1">{n.label}</h1>
      <div className="card rise d2" style={{ maxWidth: 640, marginTop: 26 }}>
        <div className="ch"><span className="tile" style={{ color: n.c }}><Hourglass size={15} /></span>What this screen will do</div>
        <p className="sent" style={{ marginTop: 14 }}>{STAGE_TEXT[k]}</p>
        <p className="note" style={{ marginTop: 14 }}>Stage 1 builds the foundation: careers, save reading, player identity, the Home screen, update checks and data backups. This module is built in stage {n.stage}.</p>
      </div>
    </div>
  );
};
