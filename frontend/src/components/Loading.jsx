// Shaped placeholder shown while a screen loads, instead of "Loading…" text.
export const Loading = ({ id = "loading", rows = 4, label = "Loading" }) => (
  <div className="skel-wrap" role="status" aria-label={label} data-testid={id}>
    <div className="skel" style={{ width: "38%", height: 18 }} />
    {Array.from({ length: rows }, (_, i) => <div key={i} className="skel" style={{ width: `${92 - i * 9}%` }} />)}
  </div>
);
