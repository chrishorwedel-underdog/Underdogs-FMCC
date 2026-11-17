import { useState } from "react";
import { Search } from "lucide-react";

export const ClubPicker = ({ clubs, onPick, busy }) => {
  const [q, setQ] = useState("");
  const shown = clubs.filter((c) => c.name.toLowerCase().includes(q.trim().toLowerCase())).slice(0, 60);
  return (
    <div className="club-pick" data-testid="setup-club-picker">
      <label className="lbl">Pick your club</label>
      <div className="club-pick-search">
        <Search size={16} />
        <input className="inp" placeholder={`Search ${clubs.length} clubs from this save`} value={q} onChange={(e) => setQ(e.target.value)} data-testid="setup-club-search" />
      </div>
      <div className="club-pick-list" role="listbox">
        {shown.map((c) => (
          <button key={c.uid} className="save-opt" disabled={busy} onClick={() => onPick(c)} data-testid={`setup-club-option-${c.uid}`}>
            <b>{c.name}</b>{c.likely && <span className="club-pick-tag">Likely match</span>}
          </button>
        ))}
        {!shown.length && <p className="muted" data-testid="setup-club-none">No club matches "{q}".</p>}
      </div>
    </div>
  );
};
