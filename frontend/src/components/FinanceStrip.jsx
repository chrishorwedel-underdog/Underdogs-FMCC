import { useState } from "react";
import { useGet } from "@/lib/ui";
import { TransferBreakdown, isTransferBox } from "@/components/TransferBreakdown";

export const FinanceStrip = () => {
  const { data } = useGet("finance", "/finance", undefined, { refetchInterval: 60000 });
  const [open, setOpen] = useState(null);
  if (!data) return null;
  return (
    <div className="fin-strip" role="list" aria-label="Club finances" data-testid="finance-strip">
      {data.items.map((f) => {
        const click = isTransferBox(f.key);
        const go = () => setOpen(f.key === "sold" ? "sales" : "buys");
        return (
          <span key={f.key} role={click ? "button" : "listitem"} tabIndex={0} className={`fin-i ${f.tone || ""}${click ? " fin-click" : ""}`}
            title={click ? `${f.reason || ""}${f.reason ? " · " : ""}Click to see this season's buys and sales` : f.reason}
            aria-label={`${f.label}: ${f.text}. ${f.reason || ""}${click ? " Opens this season's transfers." : ""}`}
            onClick={click ? go : undefined} onKeyDown={click ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } } : undefined}
            data-testid={`finance-${f.key}`}>
            <i aria-hidden="true" />{f.label}<b data-testid={`finance-${f.key}-value`}>{f.text}</b>
          </span>
        );
      })}
      {open && <TransferBreakdown start={open} onClose={() => setOpen(null)} />}
    </div>
  );
};
