import { useState } from "react";

const W = 105, H = 68;
const pos = (team, x, y) => (team === "us" ? [x * 1.05, y * 0.68] : [W - x * 1.05, H - y * 0.68]);
const COL = { us: "#4C8DFF", them: "#FF8A5B" };
const DEF = { tackle: "▲", interception: "◆", pressure: "●", clearance: "■" };

const Field = () => (
  <g fill="none" stroke="rgba(255,255,255,.18)" strokeWidth=".3">
    <rect x="0" y="0" width={W} height={H} /><line x1={W / 2} y1="0" x2={W / 2} y2={H} /><circle cx={W / 2} cy={H / 2} r="9.15" />
    <rect x="0" y="13.84" width="16.5" height="40.32" /><rect x={W - 16.5} y="13.84" width="16.5" height="40.32" />
    <rect x="0" y="24.84" width="5.5" height="18.32" /><rect x={W - 5.5} y="24.84" width="5.5" height="18.32" />
  </g>
);

const Heat = ({ pts }) => {
  const g = {};
  pts.forEach(([x, y]) => { const k = `${Math.min(11, Math.floor(x / (W / 12)))}-${Math.min(7, Math.floor(y / (H / 8)))}`; g[k] = (g[k] || 0) + 1; });
  const max = Math.max(1, ...Object.values(g));
  return Object.entries(g).map(([k, v]) => { const [i, j] = k.split("-").map(Number); return <rect key={k} x={i * (W / 12)} y={j * (H / 8)} width={W / 12} height={H / 8} fill="#4C8DFF" opacity={(v / max) * 0.75} />; });
};

export const Chalkboard = ({ m, layer, f }) => {
  const [tip, setTip] = useState(null);
  const keep = (e) => (f.team === "both" || e.team === f.team) && (f.half === "all" || (f.half === "1" ? e.minute <= 45 : e.minute > 45)) && (!f.player || e.unique_id === Number(f.player));
  const shots = m.shots.filter(keep), passes = m.passes.filter(keep).filter((p) => f.kind !== "progressive" || p.progressive).filter((p) => f.kind !== "key" || p.key), defs = m.defensive.filter(keep);
  return (
    <div style={{ position: "relative" }} data-testid="chalkboard">
      <svg viewBox={`-2 -2 ${W + 4} ${H + 4}`} style={{ width: "100%", background: "radial-gradient(ellipse at 50% 40%,#0F1F19,#0A110E 70%)", borderRadius: 14 }}>
        <Field />
        {layer === "heat" && <Heat pts={[...passes.map((p) => pos(p.team, p.x1, p.y1)), ...defs.map((d) => pos(d.team, d.x, d.y)), ...shots.map((s) => pos(s.team, s.x, s.y))]} />}
        {layer === "passes" && passes.map((p, i) => { const [a, b] = pos(p.team, p.x1, p.y1), [c, d] = pos(p.team, p.x2, p.y2); return <line key={i} x1={a} y1={b} x2={c} y2={d} stroke={p.completed ? COL[p.team] : "rgba(255,255,255,.35)"} strokeWidth={p.key ? 0.6 : 0.3} opacity={p.completed ? 0.8 : 0.5} strokeDasharray={p.completed ? "" : "1 1"} />; })}
        {layer === "defensive" && defs.map((d, i) => { const [x, y] = pos(d.team, d.x, d.y); return <text key={i} x={x} y={y} fontSize="2.4" fill={COL[d.team]} textAnchor="middle" onMouseEnter={() => setTip({ x, y, t: `${d.player} · ${d.type} · ${d.minute}'` })} onMouseLeave={() => setTip(null)}>{DEF[d.type]}</text>; })}
        {layer === "shots" && shots.map((s, i) => { const [x, y] = pos(s.team, s.x, s.y); return <circle key={i} cx={x} cy={y} r={0.8 + s.xg * 4} fill={s.outcome === "goal" ? COL[s.team] : "transparent"} stroke={COL[s.team]} strokeWidth=".35" style={{ cursor: "pointer" }}
          onMouseEnter={() => setTip({ x, y, t: `${s.player} · ${s.minute}' · xG ${s.xg} · ${s.outcome}` })} onMouseLeave={() => setTip(null)} data-testid={`shot-${i}`} />; })}
      </svg>
      {tip && <div className="tip" style={{ opacity: 1, left: `${((tip.x + 2) / (W + 4)) * 100}%`, top: `${((tip.y + 2) / (H + 4)) * 100}%`, transform: "translate(-50%,-120%)" }} data-testid="chalkboard-tip">{tip.t}</div>}
      <div className="note" style={{ marginTop: 8, display: "flex", gap: 14 }}><span style={{ color: COL.us }}>● {m.club_name} attacking →</span><span style={{ color: COL.them }}>● {m.opponent} attacking ←</span>
        {layer === "shots" && <span>Circle size = xG, filled = goal</span>}{layer === "defensive" && <span>▲ tackle ◆ interception ● pressure ■ clearance</span>}</div>
    </div>
  );
};
