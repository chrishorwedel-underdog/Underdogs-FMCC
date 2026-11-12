import { Info } from "lucide-react";

const TITLE = { filters: "Your filters rule everyone out", minutes: "Not enough minutes yet", missing: "This isn't in the save yet", nobody: "Nobody qualifies yet" };

// Says why something is empty and offers the matching fix.
export const Empty = ({ id, reason = "nobody", text, actions = [] }) => (
  <div className="empty-st" role="status" data-testid={id}>
    <Info size={16} aria-hidden="true" />
    <div style={{ flex: 1 }}>
      <b data-testid={`${id}-reason`}>{TITLE[reason]}</b>
      {text && <p>{text}</p>}
      {actions.length > 0 && <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
        {actions.map(([label, fn], i) => <button key={label} className={`btn${i === 0 ? " btn-p" : ""}`} onClick={fn} data-testid={`${id}-action-${i}`}>{label}</button>)}
      </div>}
    </div>
  </div>
);
