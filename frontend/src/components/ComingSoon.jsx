import { Hourglass } from "lucide-react";
import { STAGE_TEXT, NAV } from "@/constants/nav";

export const ComingSoon = ({ k }) => {
  const n = NAV.find((x) => x.key === k) || { label: k === "appearance" ? "Appearance" : "Ask your DOF", c: "#A78BFA" };
  return (
    <div data-testid={`coming-soon-${k}`}>
      <div className="eyebrow rise">Coming soon</div>
      <h1 className="h rise d1">{n.label}</h1>
      <div className="card rise d2" style={{ maxWidth: 640, marginTop: 26 }}>
        <div className="ch"><span className="tile" style={{ color: n.c }}><Hourglass size={15} /></span>What this screen will do</div>
        <p className="sent" style={{ marginTop: 14 }}>{STAGE_TEXT[k]}</p>
      </div>
    </div>
  );
};
