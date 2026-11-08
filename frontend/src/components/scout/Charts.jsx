import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, CartesianGrid, BarChart, Bar, Legend } from "recharts";
import { useGet } from "@/lib/ui";
import { money } from "@/lib/ui";
import { useScout } from "./ctx";

const AXES = (meta) => [["grade", "Global grade"], ["value", "Value"], ["age", "Age"], ["minutes", "Minutes"], ...(meta?.metrics || []).map((m) => [m.key, m.label]),
  ...(meta?.archetypes || []).map((a) => [`c:${a.key}`, `Computed: ${a.name}`]), ...(meta?.formulas || []).map((f) => [`f:${f.key}`, `Formula: ${f.name}`])];

const Tip = ({ active, payload }) => (active && payload?.[0] ? <div className="card" style={{ padding: 8, fontSize: 12 }}><b>{payload[0].payload.name}</b><br />{payload[0].payload.club}<br />x {payload[0].payload.x} · y {payload[0].payload.y}</div> : null);

export const ScatterTab = () => {
  const { openPlayer } = useScout();
  const [s, setS] = useState({ x: "npxg", y: "xa", mode: "p90", group: "", gender: "M" });
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const { data } = useGet("scatter", "/scout/scatter", { ...s, group: s.group || undefined });
  const axes = AXES(meta);
  const set = (k) => (e) => setS({ ...s, [k]: e.target.value });
  const pts = data?.points || [];
  return (
    <div className="card" data-testid="scatter-card">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <select className="inp" style={{ width: 260 }} value={s.x} onChange={set("x")} data-testid="scatter-x">{axes.map(([k, l]) => <option key={k} value={k}>X: {l}</option>)}</select>
        <select className="inp" style={{ width: 260 }} value={s.y} onChange={set("y")} data-testid="scatter-y">{axes.map(([k, l]) => <option key={k} value={k}>Y: {l}</option>)}</select>
        <select className="inp" style={{ width: 170 }} value={s.group} onChange={set("group")} data-testid="scatter-group"><option value="">All positions</option>{Object.entries(meta?.groups || {}).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
        <select className="inp" style={{ width: 180 }} value={s.mode} onChange={set("mode")} data-testid="scatter-mode"><option value="p90">Per 90</option><option value="total">Season totals</option><option value="adjusted">Adjusted</option></select>
      </div>
      <div style={{ height: 460, marginTop: 12 }}>
        <ResponsiveContainer>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,.05)" />
            <XAxis type="number" dataKey="x" stroke="#6B7280" fontSize={11} tickFormatter={s.x === "value" ? money : undefined} />
            <YAxis type="number" dataKey="y" stroke="#6B7280" fontSize={11} tickFormatter={s.y === "value" ? money : undefined} />
            <Tooltip content={<Tip />} />
            {data?.avg_x != null && <ReferenceLine x={data.avg_x} stroke="#F2B54A" strokeDasharray="4 4" />}
            {data?.avg_y != null && <ReferenceLine y={data.avg_y} stroke="#F2B54A" strokeDasharray="4 4" />}
            <Scatter data={pts.filter((p) => !p.own)} fill="#4C8DFF" fillOpacity={0.7} onClick={(p) => openPlayer(p.unique_id)} cursor="pointer" />
            <Scatter data={pts.filter((p) => p.own)} fill="#A3E635" onClick={(p) => openPlayer(p.unique_id)} cursor="pointer" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="note" data-testid="scatter-count">{pts.length} players with {meta?.min_minutes.percentiles}+ minutes. Dashed lines are the averages; green dots are your squad. Click a dot to open the profile.</p>
    </div>
  );
};

const COLORS = ["#4C8DFF", "#A3E635", "#F2B54A", "#F472B6", "#22D3EE", "#A78BFA", "#FB923C", "#34D399", "#E879F9", "#FACC15", "#60A5FA", "#F87171"];

export const Breakdown = ({ ids }) => {
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const [key, setKey] = useState("bpd");
  const { data } = useGet("breakdown", "/scout/breakdown", { ids: ids.join(","), key }, { enabled: ids.length > 0 });
  const parts = data?.players[0] ? Object.keys(data.players[0].parts) : [];
  const rows = (data?.players || []).map((p) => ({ name: `${p.name} (${p.score ?? "—"})`, ...p.parts }));
  return (
    <div className="card" style={{ marginTop: 16 }} data-testid="breakdown-card">
      <div className="ttl">Computed stat broken into its parts<span style={{ marginLeft: "auto" }} />
        <select className="inp" style={{ width: 240 }} value={key} onChange={(e) => setKey(e.target.value)} data-testid="breakdown-select">{meta?.archetypes.map((a) => <option key={a.key} value={a.key}>{a.name}</option>)}</select></div>
      <div style={{ height: 80 + rows.length * 54 }}>
        <ResponsiveContainer>
          <BarChart data={rows} layout="vertical" margin={{ left: 40, right: 20 }}>
            <XAxis type="number" stroke="#6B7280" fontSize={11} domain={[0, 100]} /><YAxis type="category" dataKey="name" stroke="#9CA3AF" fontSize={12} width={170} />
            <Tooltip contentStyle={{ background: "#14181D", border: "1px solid #2A2F36", fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
            {parts.map((k, i) => <Bar key={k} dataKey={k} stackId="a" fill={COLORS[i % COLORS.length]} />)}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
