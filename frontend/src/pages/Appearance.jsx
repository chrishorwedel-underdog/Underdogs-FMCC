import { useState } from "react";
import { toast } from "sonner";
import { Check, RotateCcw } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { PageHead } from "@/lib/ui";
import { ACCENTS, DEFAULTS, TEXT_SIZES, THEMES, loadAppearance, saveAppearance } from "@/lib/appearance";

const Choice = ({ on, onClick, children, id }) => (
  <button className={`btn${on ? " btn-p" : ""}`} onClick={onClick} data-testid={id}>{on && <Check size={13} />}{children}</button>
);

const Row = ({ title, note, children }) => (
  <div className="card">
    <div className="ttl">{title}</div>
    {note && <p className="note" style={{ marginTop: 4 }}>{note}</p>}
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>{children}</div>
  </div>
);

export default function Appearance() {
  const [s, setS] = useState(loadAppearance);
  const set = (p) => { const n = { ...s, ...p }; setS(n); saveAppearance(n); };
  return (
    <div data-testid="appearance-page">
      <PageHead eyebrow="How FMCC looks on your screen" title="Appearance">
        <button className="btn" onClick={() => { set(DEFAULTS); toast.success("Back to the standard look"); }} data-testid="appearance-reset"><RotateCcw size={13} />Reset</button>
      </PageHead>
      <div style={{ display: "grid", gap: 16 }}>
        <Row title="Text size" note="Makes all text, buttons and boxes bigger, so everything stays in proportion.">
          {TEXT_SIZES.map(([v, l]) => <Choice key={v} on={s.text === v} onClick={() => set({ text: v })} id={`appearance-text-${v}`}>{l} <small style={{ opacity: 0.7 }}>{v}%</small></Choice>)}
        </Row>
        <Row title="Theme" note="The background colours of the app.">
          {Object.entries(THEMES).map(([k, t]) => <Choice key={k} on={s.theme === k} onClick={() => set({ theme: k })} id={`appearance-theme-${k}`}>{t.label}</Choice>)}
        </Row>
        <Row title="Accent colour" note="Used for highlights, selected tabs and main buttons.">
          {ACCENTS.map(([l, c]) => (
            <button key={c} className="btn" onClick={() => set({ accent: c })} style={{ borderColor: s.accent === c ? c : undefined }} data-testid={`appearance-accent-${l.toLowerCase()}`}>
              <span style={{ width: 14, height: 14, borderRadius: 99, background: c, display: "inline-block" }} />{l}{s.accent === c && <Check size={13} />}</button>))}
        </Row>
        <div className="card">
          <div className="row"><div style={{ flex: 1 }}>Animations<small>Slide and fade effects when things open or change</small></div><Switch checked={s.motion} onCheckedChange={(v) => set({ motion: v })} data-testid="appearance-motion" /></div>
          <div className="row"><div style={{ flex: 1 }}>Film grain<small>A faint texture over the background</small></div><Switch checked={s.grain} onCheckedChange={(v) => set({ grain: v })} data-testid="appearance-grain" /></div>
        </div>
        <p className="note">These settings are saved on this computer and apply straight away.</p>
      </div>
    </div>
  );
}
