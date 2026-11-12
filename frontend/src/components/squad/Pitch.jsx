import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const Lines = () => (
  <svg className="lines" viewBox="0 0 68 105" preserveAspectRatio="none" fill="none" stroke="rgba(255,255,255,.13)" strokeWidth="1.2">
    <rect x="0" y="0" width="68" height="105" rx="1" vectorEffect="non-scaling-stroke" /><line x1="0" y1="52.5" x2="68" y2="52.5" vectorEffect="non-scaling-stroke" />
    <ellipse cx="34" cy="52.5" rx="9.15" ry="9.15" vectorEffect="non-scaling-stroke" />
    <rect x="13.84" y="0" width="40.32" height="16.5" vectorEffect="non-scaling-stroke" /><rect x="24.84" y="0" width="18.32" height="5.5" vectorEffect="non-scaling-stroke" />
    <rect x="13.84" y="88.5" width="40.32" height="16.5" vectorEffect="non-scaling-stroke" /><rect x="24.84" y="99.5" width="18.32" height="5.5" vectorEffect="non-scaling-stroke" />
  </svg>
);

const Token = ({ slot, uid, plan, onPick, slots }) => {
  const p = plan.players[uid];
  const rating = plan.depth[slot.key]?.find((r) => r.unique_id === uid)?.rating;
  const drop = (e) => { e.preventDefault(); const from = e.dataTransfer.getData("text/fmcc-slot"); if (from && from !== slot.key) onPick(slot.key, slots[from]); };
  return (
    <div className="p" style={{ left: `${slot.x}%`, top: `${slot.y}%` }} data-testid={`pitch-slot-${slot.key}`}
      draggable onDragStart={(e) => e.dataTransfer.setData("text/fmcc-slot", slot.key)} onDragOver={(e) => e.preventDefault()} onDrop={drop}>
      <div className="tip"><b>{p?.name}</b><span>{slot.role_name} · rating {rating}</span></div>
      <Popover>
        <PopoverTrigger asChild>
          <button className={`tok${p?.u21 ? " y" : ""}`} data-testid={`pitch-token-${slot.key}`}>{slot.pos}{p?.u21 && <em>U21</em>}</button>
        </PopoverTrigger>
        <PopoverContent className="w-72 p-2" style={{ background: "var(--s2)" }} data-testid={`pitch-options-${slot.key}`}>
          <div className="gl" style={{ fontSize: 10.5, letterSpacing: ".14em", textTransform: "uppercase", color: "var(--dim)", padding: "6px 8px" }}>{slot.label} · {slot.role_name}</div>
          {plan.depth[slot.key].map((r) => (
            <div key={r.unique_id} className={`pi${r.unique_id === uid ? " sel" : ""}`} onClick={() => onPick(slot.key, r.unique_id)} data-testid={`pitch-pick-${slot.key}-${r.unique_id}`}>
              {plan.players[r.unique_id].name} <span style={{ color: "var(--dim)", fontSize: 11.5 }}>{plan.players[r.unique_id].age}</span>{plan.players[r.unique_id].u21 && <span className="tag st g">U21</span>}<small className="mono">{r.rating}</small>
            </div>
          ))}
        </PopoverContent>
      </Popover>
      <b>{p?.name || "—"}</b><small>{rating ?? ""}{p?.u21 ? " · U21" : ""}</small>
    </div>
  );
};

export const Pitch = ({ plan, slots, onPick }) => (
  <div className="card pitchc rise d1" data-testid="pitch">
    <Lines />
    {plan.formation.slots.map((s) => <Token key={s.key} slot={s} uid={slots[s.key]} slots={slots} plan={plan} onPick={onPick} />)}
  </div>
);
