import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { applyAppearance, loadAppearance } from "@/lib/appearance";

const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const mix = (hex, t) => "#" + [1, 3, 5].map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) * (1 - t)).toString(16).padStart(2, "0")).join("");

// darkened until FMCC's light top-bar text stays readable on it
export const readableTop = (hex) => {
  let t = 0;
  while (lum(mix(hex, t)) > 0.07 && t < 0.9) t += 0.05;
  return mix(hex, t);
};

const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };

// the trim colour lightened until it stands out on FMCC's dark panels, so highlights and buttons stay readable
export const kitAccent = (hex) => {
  let t = 0, c = hex;
  while (contrast(c, "#121519") < 4.5 && t < 0.9) { t += 0.05; c = "#" + [1, 3, 5].map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) + (255 - parseInt(hex.slice(i, i + 2), 16)) * t).toString(16).padStart(2, "0")).join(""); }
  return c;
};

// the trim colour for the badge letters when it reads well on the main colour, else white or black
export const crestText = (bg, trim) => (trim && contrast(bg, trim) >= 3 ? trim : contrast(bg, "#FFFFFF") >= contrast(bg, "#000000") ? "#FFFFFF" : "#000000");

export const ClubColours = () => {
  const { data } = useGet("club-colours", "/club-colours");
  useEffect(() => {
    const root = document.documentElement;
    if (data?.primary) {
      root.style.setProperty("--club-top", readableTop(data.primary));
      root.style.setProperty("--club-line", data.secondary || data.primary);
      root.style.setProperty("--club-crest", data.primary);
      root.style.setProperty("--club-crest-fg", crestText(data.primary, data.secondary));
    } else {
      ["--club-top", "--club-line", "--club-crest", "--club-crest-fg"].forEach((k) => root.style.removeProperty(k));
    }
    window.__fmccKitAccent = data?.secondary || data?.primary ? kitAccent(data.secondary || data.primary) : null;
    applyAppearance(loadAppearance());
  }, [data]);
  return null;
};

export const ClubColoursCard = () => {
  const { data } = useGet("club-colours", "/club-colours");
  const act = useAct();
  const [p, setP] = useState(null);
  const [s, setS] = useState(null);
  useEffect(() => { if (data) { setP(data.primary || "#2A2240"); setS(data.secondary || "#A98BFF"); } }, [data]);
  if (!data || !p) return null;
  const src = { you: "Colours you picked", save: "Read from your save", null: "Not in your save, so the top bar uses FM27's colours" }[data.source];
  return (
    <div className="card" style={{ marginTop: 12 }} data-testid="club-colours-card">
      <div className="ttl">Your club's colours (FM27 theme top bar)</div>
      <p className="note" data-testid="club-colours-source">{src}. Colours are darkened when needed so the text stays readable.</p>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 8 }}>
        <label className="note" style={{ margin: 0, display: "flex", gap: 6, alignItems: "center" }}>Main<input type="color" value={p} onChange={(e) => setP(e.target.value)} data-testid="club-colour-primary" /></label>
        <label className="note" style={{ margin: 0, display: "flex", gap: 6, alignItems: "center" }}>Trim<input type="color" value={s} onChange={(e) => setS(e.target.value)} data-testid="club-colour-secondary" /></label>
        <span style={{ width: 120, height: 26, borderRadius: 6, background: readableTop(p), borderBottom: `3px solid ${s}`, display: "inline-flex", alignItems: "center", paddingLeft: 4 }} data-testid="club-colour-preview">
          <span style={{ width: 20, height: 20, borderRadius: 6, background: p, border: `1px solid ${s}`, color: crestText(p, s), fontSize: 9, fontWeight: 700, display: "grid", placeItems: "center" }} data-testid="club-colour-crest-preview">FC</span></span>
        <button className="btn btn-p" onClick={() => act(() => api.put("/club-colours", { primary: p, secondary: s }), "Club colours saved", ["club-colours"])} data-testid="club-colours-save">Save</button>
        {data.source === "you" && <button className="btn" onClick={() => act(() => api.delete("/club-colours"), "Using your save's colours again", ["club-colours"])} data-testid="club-colours-reset">Use save colours</button>}
      </div>
    </div>
  );
};
