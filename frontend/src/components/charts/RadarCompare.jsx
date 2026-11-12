import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Plus, X, Printer, ImageDown } from "lucide-react";
import { api } from "@/lib/api";
import { useAct, TabBar } from "@/lib/ui";
import { attributeRadar } from "@/components/charts/DataHub";
import { Empty } from "@/components/Empty";

export const COLOURS = ["#4C8DFF", "#F5C542", "#34D399", "#F472B6"];
const KIND = [["role", "Role fit"], ["phases", "Phases of play"], ["attributes", "Attributes by area"]];

const axesFor = (d, kind) => {
  if (kind === "role") return d.keys.map((k) => ({ axis: d.labels[k].replace(" / 90", ""), ...Object.fromEntries(d.players.map((p, i) => [`p${i}`, p.role[k]])) }));
  if (kind === "phases") return ["finishing", "creating", "carrying", "defending"].map((k) => ({ axis: k[0].toUpperCase() + k.slice(1), ...Object.fromEntries(d.players.map((p, i) => [`p${i}`, p.phases[k]])) }));
  const per = d.players.map((p) => Object.fromEntries((p.attributes ? attributeRadar(p.attributes) : []).map((a) => [a.axis, a.value])));
  return [...new Set(per.flatMap((x) => Object.keys(x)))].map((axis) => ({ axis, ...Object.fromEntries(per.map((x, i) => [`p${i}`, x[axis]])) }));
};
const missing = (d, kind, p) => (kind === "attributes" ? !p.attributes : kind === "phases" ? !Object.keys(p.phases).length : d.keys.every((k) => p.role[k] == null));

const Picker = ({ onPick, exclude }) => {
  const act = useAct();
  const [q, setQ] = useState("");
  const [rows, setRows] = useState(null);
  const find = () => act(() => api.post("/scout/players", { q, limit: 8, view: "full", mode: "p90", gender: "M", source: "save", min_age: 15, max_age: 45, min_minutes: 0, sort: "grade", dir: "desc" }), null, []).then((r) => r && setRows(r.rows.filter((x) => !exclude.includes(x.unique_id))));
  return (
    <div data-testid="radar-picker">
      <div style={{ display: "flex", gap: 8 }}>
        <input className="inp" style={{ flex: 1 }} placeholder="Find a player to compare with" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && q.trim() && find()} data-testid="radar-search" />
        <button className="btn btn-p" disabled={!q.trim()} onClick={find} data-testid="radar-search-button">Find</button></div>
      {rows && (rows.length ? rows.map((r) => <div className="row" key={r.unique_id}><div style={{ flex: 1 }}>{r.name}<small>{r.club} · {r.age}</small></div>
        <button className="btn" onClick={() => { onPick(r.unique_id); setRows(null); setQ(""); }} data-testid={`radar-pick-${r.unique_id}`}><Plus size={13} />Add</button></div>)
        : <Empty id="radar-pick-empty" reason="notfound" text="Check the spelling or try just the surname." />)}
    </div>
  );
};

const fg = (hex) => { const h = (hex || "").replace("#", ""); if (h.length !== 6) return "#fff"; const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); return r * 0.299 + g * 0.587 + b * 0.114 > 150 ? "#0B0D10" : "#FFFFFF"; };

const useBrand = () => {
  const { data: st } = useQuery({ queryKey: ["state"], queryFn: () => api.get("/state").then((r) => r.data) });
  const { data: cc } = useQuery({ queryKey: ["club-colours"], queryFn: () => api.get("/club-colours").then((r) => r.data) });
  const cs = getComputedStyle(document.documentElement);
  const primary = cc?.primary || cs.getPropertyValue("--acc").trim() || "#4C8DFF";
  const secondary = cc?.secondary || cs.getPropertyValue("--s3").trim() || "#191D23";
  const club = st?.career?.club_name || "";
  return { primary, secondary, club, initials: club.slice(0, 2).toUpperCase(), fromSave: !!cc?.primary };
};

let printing = false;
const printCard = () => {
  if (printing) return;
  printing = true;
  const root = document.documentElement;
  root.classList.add("printing-radar");
  const done = () => { root.classList.remove("printing-radar"); window.removeEventListener("afterprint", done); setTimeout(() => { printing = false; }, 300); };
  window.addEventListener("afterprint", done);
  window.print();
  setTimeout(() => { if (printing) done(); }, 1500);
};

const saveImage = (el, name, brand) => {
  const svg = el.querySelector("svg.recharts-surface");
  if (!svg) return;
  const { width, height } = svg.getBoundingClientRect();
  const img = new Image();
  const cs = getComputedStyle(document.documentElement);
  const txt = new XMLSerializer().serializeToString(svg).replace(/var\(--([a-z0-9]+)\)/g, (_, v) => cs.getPropertyValue(`--${v}`).trim() || "#888");
  img.onload = () => {
    const c = document.createElement("canvas");
    c.width = width * 2; c.height = (height + 96) * 2;
    const g = c.getContext("2d");
    g.scale(2, 2); g.fillStyle = cs.getPropertyValue("--bg") || "#08090B"; g.fillRect(0, 0, width, height + 96);
    g.fillStyle = brand.primary; g.fillRect(0, 0, width, 56);
    g.fillStyle = brand.secondary; g.fillRect(0, 56, width, 4);
    g.fillStyle = brand.secondary; g.beginPath(); g.arc(34, 28, 18, 0, Math.PI * 2); g.fill();
    g.fillStyle = fg(brand.secondary); g.font = "700 13px sans-serif"; g.textAlign = "center"; g.fillText(brand.initials, 34, 33); g.textAlign = "left";
    g.fillStyle = fg(brand.primary); g.font = "700 16px sans-serif"; g.fillText(brand.club, 62, 26);
    g.font = "500 12px sans-serif"; g.fillText(name, 62, 44);
    g.drawImage(img, 0, 70, width, height);
    const a = document.createElement("a"); a.href = c.toDataURL("image/png"); a.download = "fmcc-radar-compare.png"; a.click();
  };
  img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(txt)}`;
};

export const RadarCompare = ({ ids: start = [], view = "full" }) => {
  const act = useAct();
  const [ids, setIds] = useState(start.slice(0, 4));
  const [kind, setKind] = useState("role");
  const [role, setRole] = useState(null);
  const [d, setD] = useState(null);
  const card = useRef(null);
  const brand = useBrand();
  useEffect(() => { setIds(start.slice(0, 4)); }, [start.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (ids.length < 2) { setD(null); return; }
    act(() => api.post("/scout/radar-compare", { ids, role, view }), null, []).then((r) => r && setD(r));
  }, [ids.join(","), role, view]); // eslint-disable-line react-hooks/exhaustive-deps
  const data = d ? axesFor(d, kind) : [];
  const gone = d ? d.players.filter((p) => missing(d, kind, p)) : [];
  return (
    <div style={{ display: "grid", gap: 12, gridTemplateColumns: "minmax(0,1fr)" }} data-testid="radar-compare">
      {ids.length < 4 && <Picker onPick={(u) => setIds([...ids, u])} exclude={ids} />}
      {ids.length < 2 && <p className="note">Add {2 - ids.length} more player{ids.length ? "" : "s"} to compare. You can compare up to four.</p>}
      {d && <div className="hub-card print-card radar-branded" ref={card} style={{ borderTop: `4px solid ${brand.primary}` }} data-testid="radar-card">
        <div className="radar-brand" style={{ background: brand.primary, color: fg(brand.primary) }} data-testid="radar-brand">
          <span className="radar-crest" style={{ background: brand.secondary, color: fg(brand.secondary) }} data-testid="radar-crest">{brand.initials}</span>
          <span><b data-testid="radar-club-name">{brand.club}</b><small>{d.players.map((p) => p.name).join(" vs ")}</small></span>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: 8 }}>
          <TabBar id="radar-kind" value={kind} onChange={setKind} tabs={KIND} />
          {kind === "role" && <select className="inp" style={{ width: 220 }} value={d.role} onChange={(e) => setRole(e.target.value)} aria-label="Role" data-testid="radar-role">{d.roles.map((r) => <option key={r}>{r}</option>)}</select>}
          <span style={{ marginLeft: "auto" }} />
          <button className="btn no-print" onClick={() => saveImage(card.current, d.players.map((p) => p.name).join(" vs "), brand)} data-testid="radar-save-image"><ImageDown size={13} />Save image</button>
          <button className="btn no-print" onClick={printCard} data-testid="radar-print"><Printer size={13} />Print</button>
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
          {d.players.map((p, i) => <span key={p.unique_id} className="hchip" style={{ borderColor: COLOURS[i] }} data-testid={`radar-player-${p.unique_id}`}>
            <i style={{ width: 10, height: 10, borderRadius: 99, background: COLOURS[i], display: "inline-block" }} />{p.name}
            <button className="ib no-print" style={{ width: 22, height: 22 }} aria-label={`Remove ${p.name}`} onClick={() => setIds(ids.filter((x) => x !== p.unique_id))} data-testid={`radar-remove-${p.unique_id}`}><X size={11} /></button></span>)}
        </div>
        {gone.length > 0 && <Empty id="radar-missing" reason={kind === "attributes" ? "missing" : "minutes"} text={`${gone.map((p) => p.name).join(", ")} ${kind === "attributes" ? "has no attributes in this view" : "hasn't played enough minutes for these stats"}, so ${gone.length > 1 ? "they're" : "he's"} left off this chart.`} />}
        <div style={{ height: 340 }} aria-label={`${KIND.find((k) => k[0] === kind)[1]} radar for ${d.players.map((p) => p.name).join(", ")}`}>
          <ResponsiveContainer>
            <RadarChart data={data} outerRadius="66%" margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
              <PolarGrid stroke="var(--line2)" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: "var(--mut)", fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, kind === "attributes" ? 20 : 100]} tick={false} axisLine={false} />
              {d.players.map((p, i) => !missing(d, kind, p) && <Radar key={p.unique_id} name={p.name} dataKey={`p${i}`} stroke={COLOURS[i]} fill={COLOURS[i]} fillOpacity={0.14} strokeWidth={2} />)}
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "var(--s2)", border: "1px solid var(--line2)", fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        {kind === "role" && d.verdict && <div className="impact" data-testid="radar-verdict"><b>{d.verdict.text}.</b>
          <small style={{ display: "block", color: "var(--mut)", marginTop: 3 }}>Biggest gaps: {d.verdict.gaps.map((g) => `${g.label} (${g.a} vs ${g.b})`).join(", ")}. Percentiles against players in the same position; guidance, not a guarantee.{d.players.length > 2 ? " The verdict compares the first two players." : ""}</small></div>}
        {d.players.length > 2 && <table className="tbl" style={{ marginTop: 10 }} data-testid="radar-gap-table"><thead><tr><th>Area</th>{d.players.map((p, i) => <th key={p.unique_id} style={{ color: COLOURS[i] }}>{p.name}</th>)}</tr></thead>
          <tbody>{data.map((r) => <tr key={r.axis} style={{ cursor: "default" }}><td>{r.axis}</td>{d.players.map((p, i) => <td key={p.unique_id} className="mono">{r[`p${i}`] ?? "—"}</td>)}</tr>)}</tbody></table>}
      </div>}
    </div>
  );
};
