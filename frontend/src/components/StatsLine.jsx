export const StatsLine = ({ line, id }) => (
  <span data-testid={id}>
    {line.map((s, j) => <span key={s.key}>{j > 0 && " · "}<span className="mono">{s.value}</span> {s.label}</span>)}
  </span>
);
