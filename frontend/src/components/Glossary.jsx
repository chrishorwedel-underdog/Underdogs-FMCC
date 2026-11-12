import { useEffect, useRef, useState } from "react";
import { BookOpen, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { GLOSSARY, findTerm } from "@/constants/glossary";

export const openGlossary = (text = "") => window.dispatchEvent(new CustomEvent("fmcc-glossary", { detail: text }));

const useHeaderTrigger = () => {
  const [spot, setSpot] = useState(null);
  useEffect(() => {
    const show = (e) => {
      const th = e.target.closest?.("thead th");
      if (th) { setSpot({ th }); }
    };
    const hide = () => setSpot((s) => (s ? { th: s.th } : s));
    document.addEventListener("mouseover", show);
    document.addEventListener("focusin", show);
    window.addEventListener("scroll", hide, true);
    return () => { document.removeEventListener("mouseover", show); document.removeEventListener("focusin", show); window.removeEventListener("scroll", hide, true); };
  }, []);
  return [spot, setSpot];
};

const Entry = ({ g, active }) => {
  const ref = useRef(null);
  useEffect(() => { if (active) { ref.current?.scrollIntoView({ block: "center" }); } }, [active]);
  return (
    <div ref={ref} className={`gloss-item${active ? " on" : ""}`} data-testid={`glossary-term-${g.keys[0].replace(/[^a-z0-9]+/g, "-")}`}>
      <div className="gloss-term">{g.term}{g.names[0] !== g.term && <span className="gloss-short">{g.names[0]}</span>}</div>
      <div className="gloss-plain">{g.plain}</div>
    </div>
  );
};

export const GlossaryHost = () => {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [focus, setFocus] = useState(null);
  const [spot, setSpot] = useHeaderTrigger();
  const r = spot?.th?.isConnected ? spot.th.getBoundingClientRect() : null;
  useEffect(() => {
    const on = (e) => { const hit = findTerm(e.detail); setFocus(hit?.term || null); setQ(""); setOpen(true); };
    window.addEventListener("fmcc-glossary", on);
    return () => { window.removeEventListener("fmcc-glossary", on); };
  }, []);
  const n = q.trim().toLowerCase();
  const list = n ? GLOSSARY.filter((g) => g.keys.some((k) => k.includes(n)) || g.plain.toLowerCase().includes(n)) : GLOSSARY;
  return (
    <>
      {r && r.width > 0 && !open && (
        <button className="gloss-btn" style={{ top: r.top + 2, left: r.right - 20 }} aria-label="What do these columns mean?" title="What does this mean?"
          data-testid="glossary-header-button" onMouseDown={(e) => e.preventDefault()} onClick={(e) => { e.stopPropagation(); openGlossary(spot.th.innerText); setSpot(null); }}>?</button>
      )}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="gloss-dialog" data-testid="glossary-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><BookOpen size={18} /> Stat glossary</DialogTitle>
            <DialogDescription>Every stat and column name in plain words.</DialogDescription>
          </DialogHeader>
          <div className="gloss-search">
            <Input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search, e.g. xA or tackles" data-testid="glossary-search-input" />
            {q && <button onClick={() => setQ("")} aria-label="Clear search" data-testid="glossary-clear-button"><X size={14} /></button>}
          </div>
          <div className="gloss-list" data-testid="glossary-list">
            {list.map((g) => <Entry key={g.term} g={g} active={!n && g.term === focus} />)}
            {!list.length && <div className="gloss-plain" data-testid="glossary-empty">No stat matches "{q}".</div>}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
