import { useGet } from "@/lib/ui";

export const FinanceStrip = () => {
  const { data } = useGet("finance", "/finance", undefined, { refetchInterval: 60000 });
  if (!data) return null;
  return (
    <div className="fin-strip" role="list" aria-label="Club finances" data-testid="finance-strip">
      {data.items.map((f) => (
        <span key={f.key} role="listitem" tabIndex={0} className={`fin-i ${f.tone || ""}`} title={f.reason} aria-label={`${f.label}: ${f.text}. ${f.reason || ""}`} data-testid={`finance-${f.key}`}>
          <i aria-hidden="true" />{f.label}<b data-testid={`finance-${f.key}-value`}>{f.text}</b>
        </span>
      ))}
    </div>
  );
};
