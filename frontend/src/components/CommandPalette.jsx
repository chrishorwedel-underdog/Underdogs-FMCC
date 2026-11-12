import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { NAV, TOP_LINKS, HOME } from "@/constants/nav";
import { openGlossary } from "@/components/Glossary";

const SCREENS = [...[HOME, ...NAV].map((n) => ({ group: "Screens", label: n.label, sub: n.sub, to: n.to })),
  ...TOP_LINKS.map((n) => ({ group: "Screens", label: n.label, sub: n.key === "safety" ? "Backups, save checks and change record" : n.key === "extras" ? "NG_Regens, Real Name Fix and other packs" : n.key === "appearance" ? "Text size, theme and colours" : "Coming soon", to: n.to })),
  { group: "Screens", label: "Connections", sub: "Match add-on and live game editor", to: "/connections" },
  { group: "Screens", label: "Settings", sub: "Careers, updates and backups", to: "/settings" },
  { group: "Screens", label: "Game changes", sub: "Queue, batches and audit trail", to: "/changes" },
  { group: "Actions", label: "Check for updates", sub: "Settings", to: "/settings?check=1" },
  { group: "Actions", label: "Back up my data now", sub: "Settings", to: "/settings?backup=1" },
  { group: "Actions", label: "Stat glossary", sub: "Every stat and column name in plain words", to: "#glossary", words: "glossary stats terms meaning columns help", act: () => openGlossary() }];

export const CommandPalette = ({ open, onClose }) => {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const { data: players = [] } = useQuery({ queryKey: ["search", q], queryFn: () => api.get("/players/search", { params: { q } }).then((r) => r.data), enabled: open });
  useEffect(() => { if (open) { setQ(""); setSel(0); } }, [open]);
  if (!open) return null;
  const ql = q.toLowerCase();
  const items = [...players.map((p) => ({ group: "Players", label: p.name, sub: `${p.age} · ${p.positions.join(", ")}`, to: `/squad?player=${p.unique_id}` })),
    ...SCREENS.filter((s) => `${s.label} ${s.words || ""}`.toLowerCase().includes(ql))];
  const run = (i) => { const it = items[i]; if (it) { onClose(); it.act ? it.act() : nav(it.to); } };
  const onKey = (e) => {
    if (e.key === "Escape") onClose();
    if (e.key === "ArrowDown") setSel((s) => Math.min(items.length - 1, s + 1));
    if (e.key === "ArrowUp") setSel((s) => Math.max(0, s - 1));
    if (e.key === "Enter") run(sel);
  };
  let last = "";
  return (
    <div className="ov" onClick={(e) => e.target === e.currentTarget && onClose()} data-testid="command-palette">
      <div className="pal">
        <input autoFocus value={q} onChange={(e) => { setQ(e.target.value); setSel(0); }} onKeyDown={onKey}
          placeholder="Search players, screens or actions…" data-testid="command-palette-input" />
        <div className="g">
          {items.length === 0 && <div className="gl">No matches</div>}
          {items.map((it, i) => {
            const head = it.group !== last ? <div className="gl">{(last = it.group)}</div> : null;
            return (
              <div key={`${it.group}-${it.to}-${i}`}>
                {head}
                <div className={`pi${i === sel ? " sel" : ""}`} onMouseEnter={() => setSel(i)} onClick={() => run(i)} data-testid={`palette-item-${i}`}>
                  {it.label}<small>{it.sub}</small>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
