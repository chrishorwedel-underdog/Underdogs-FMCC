import { useRef, useState } from "react";
import { usePersist } from "@/lib/remember";

const MIN = 50;

// Column widths the user can drag (or nudge with arrow keys); remembered per career.
export const useColWidths = (key, defaults) => {
  const [saved, setSaved] = usePersist(`colw:${key}`, {});
  const [live, setLive] = useState(null);
  const drag = useRef(null);
  const widths = { ...defaults, ...saved, ...(live || {}) };
  const start = (col, e) => {
    e.preventDefault();
    drag.current = { col, x: e.clientX, w: widths[col] };
    const move = (ev) => { const d = drag.current; setLive({ [d.col]: Math.max(MIN, Math.round(d.w + ev.clientX - d.x)) }); };
    const up = (ev) => {
      const d = drag.current;
      setSaved((s) => ({ ...s, [d.col]: Math.max(MIN, Math.round(d.w + ev.clientX - d.x)) }));
      setLive(null);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  const nudge = (col, by) => setSaved((s) => ({ ...s, [col]: Math.max(MIN, (s[col] ?? defaults[col]) + by) }));
  const reset = () => setSaved({});
  const total = Object.keys(defaults).reduce((a, k) => a + widths[k], 0);
  return { widths, start, nudge, reset, total, changed: Object.keys(saved).length > 0 };
};

export const ColGroup = ({ cols, c }) => <colgroup>{cols.map((k) => <col key={k} style={{ width: c.widths[k] }} />)}</colgroup>;

export const ResizeTh = ({ col, c, label, className = "", title, id }) => (
  <th className={`rz-th ${className}`} title={title}>
    {label}
    <span className="rz-h" role="separator" aria-orientation="vertical" aria-label={`Resize ${label || "column"}`} tabIndex={0}
      onPointerDown={(e) => c.start(col, e)}
      onKeyDown={(e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); c.nudge(col, e.key === "ArrowLeft" ? -10 : 10); } }}
      data-testid={`${id}-resize-${col}`} />
  </th>
);
