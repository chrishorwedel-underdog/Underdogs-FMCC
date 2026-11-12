import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";

const GROUPS = {
  Attacking: ["finishing", "long_shots", "off_the_ball", "composure", "heading"],
  Creativity: ["passing", "vision", "technique", "flair", "first_touch", "crossing"],
  Dribbling: ["dribbling", "agility", "balance", "technique"],
  Defending: ["tackling", "marking", "positioning", "anticipation", "concentration"],
  Physical: ["pace", "acceleration", "strength", "stamina", "jumping_reach", "natural_fitness"],
  Mental: ["decisions", "determination", "teamwork", "work_rate", "bravery", "leadership"],
  Goalkeeping: ["handling", "reflexes", "one_on_ones", "aerial_reach", "command_of_area", "kicking"],
};
const mid = (v) => (Array.isArray(v) ? (v[0] + v[1]) / 2 : v);
const shown = (v) => (Array.isArray(v) ? (v[0] === v[1] ? v[0] : `${v[0]}–${v[1]}`) : v);

// 1-20 attribute colour, Data Hub style: red < 8, amber < 12, accent < 16, green above.
export const attrColour = (v) => (v == null ? "var(--s3)" : v >= 16 ? "var(--grn)" : v >= 12 ? "var(--acc)" : v >= 8 ? "var(--amb)" : "var(--red)");
const pctColour = (p) => (p == null ? "var(--s3)" : p >= 80 ? "var(--grn)" : p >= 60 ? "var(--acc)" : p >= 40 ? "var(--amb)" : "var(--red)");

export const RadarCard = ({ id, title, data, max = 100, unit = "", height = 240 }) => (
  <figure className="hub-card" data-testid={id} aria-label={`${title}: ${data.map((d) => `${d.axis} ${d.value}${unit}`).join(", ")}`}>
    <figcaption className="hub-h">{title}</figcaption>
    <div style={{ height }} aria-hidden="true">
      <ResponsiveContainer>
        <RadarChart data={data} outerRadius="62%" margin={{ top: 10, right: 34, bottom: 10, left: 34 }}>
          <PolarGrid stroke="var(--line2)" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: "var(--mut)", fontSize: 11 }} />
          <PolarRadiusAxis domain={[0, max]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke="var(--acc)" fill="var(--acc)" fillOpacity={0.28} strokeWidth={2} />
          <Tooltip contentStyle={{ background: "var(--s2)", border: "1px solid var(--line2)", fontSize: 12 }} formatter={(v) => [`${v}${unit}`, ""]} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  </figure>
);

export const attributeRadar = (attrs) => Object.entries(GROUPS)
  .filter(([axis]) => axis !== "Goalkeeping" || mid(attrs.handling) >= 8 || mid(attrs.reflexes) >= 8)
  .map(([axis, keys]) => { const vs = keys.map((k) => mid(attrs[k])).filter((v) => v != null); return vs.length ? { axis, value: Math.round((vs.reduce((a, b) => a + b, 0) / vs.length) * 10) / 10 } : null; })
  .filter(Boolean);

export const AttrHeatmap = ({ id, title, attrs }) => (
  <div className="hub-card" data-testid={id}>
    <div className="hub-h">{title}</div>
    <div className="heat-grid" role="list">
      {Object.entries(attrs).map(([k, v]) => (
        <div key={k} role="listitem" className="heat-cell" style={{ "--hc": attrColour(mid(v)) }} title={`${k.replace(/_/g, " ")}: ${shown(v)}`} data-testid={`${id}-${k}`}>
          <span>{k.replace(/_/g, " ")}</span><b className="mono">{shown(v)}</b>
        </div>))}
    </div>
  </div>
);

export const MetricHeatmap = ({ id, title, rows, cols, label }) => (
  <div className="hub-card" style={{ overflowX: "auto" }} data-testid={id}>
    <div className="hub-h">{title}</div>
    <table className="tbl heat-tbl">
      <caption className="sr-only">{title}. Each cell is a percentile from 0 to 100.</caption>
      <thead><tr><th scope="col">Player</th>{cols.map((c) => <th scope="col" key={c} title={label?.[c] || c}>{label?.[c] || c}</th>)}</tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.name} style={{ cursor: "default" }}><th scope="row" style={{ textAlign: "left" }}>{r.name}</th>
          {cols.map((c) => <td key={c} className="mono" style={{ background: `color-mix(in srgb, ${pctColour(r.values[c])} 30%, transparent)` }}>{r.values[c] ?? "—"}</td>)}</tr>))}</tbody>
    </table>
  </div>
);
