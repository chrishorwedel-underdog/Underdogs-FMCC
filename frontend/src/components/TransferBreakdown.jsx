import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { useGet, TabBar } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { openPlayer } from "@/components/player/PlayerPanel";

const money = (v) => (v == null ? "Fee not in save" : v >= 1e6 ? `£${(v / 1e6).toFixed(1)}m` : `£${Math.round(v / 1000)}k`);
const CLICKABLE = ["spent", "sold", "net"];
export const isTransferBox = (k) => CLICKABLE.includes(k);

const List = ({ rows, kind }) => !rows.length
  ? <p className="note" data-testid={`transfers-${kind}-empty`}>{kind === "buys" ? "No players bought this season yet." : "No players sold this season yet."}</p>
  : <div style={{ overflowX: "auto" }}><table className="tbl" data-testid={`transfers-${kind}-table`}>
    <thead><tr><th>Player</th><th>{kind === "buys" ? "From" : "To"}</th><th>Date</th><th style={{ textAlign: "right" }}>Fee</th></tr></thead>
    <tbody>{rows.map((t) => <tr key={t.unique_id} onClick={() => openPlayer(t.unique_id)} style={{ cursor: "pointer" }} data-testid={`transfers-${kind}-${t.unique_id}`}>
      <td><b>{t.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{t.age} · {t.positions.join(", ")}</small></td>
      <td>{t.other_club || "—"}</td><td className="mono">{t.date || "—"}</td>
      <td className="mono" style={{ textAlign: "right", color: t.fee == null ? "var(--dim)" : undefined }}>{money(t.fee)}</td></tr>)}</tbody></table></div>;

export const TransferBreakdown = ({ start, onClose }) => {
  const [tab, setTab] = useState(start);
  const { data } = useGet("finance-transfers", "/finance/transfers");
  const net = data ? data.total_out - data.total_in : 0;
  const anyFee = data && [...data.buys, ...data.sales].some((t) => t.fee != null);
  const tot = (v) => (anyFee ? money(v) : "No fees recorded");
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl" data-testid="transfers-dialog">
        <DialogHeader><DialogTitle>This season's transfers</DialogTitle>
          <DialogDescription>{data?.season_start ? `Since ${data.season_start}, from what FMCC saw in your save. Fees the save doesn't record are shown as missing, never guessed.` : "Read a save first."}</DialogDescription></DialogHeader>
        {!data ? <Loading id="transfers-loading" rows={4} label="Loading transfers" /> : <>
          <div className="tr-sum" data-testid="transfers-summary">
            <span>Bought <b className="mono">{tot(data.total_in)}</b></span><span>Sold <b className="mono">{tot(data.total_out)}</b></span>
            {anyFee && <span>Net <b className="mono" style={{ color: net >= 0 ? "var(--grn)" : "#F5C542" }}>{net > 0 ? "+" : net < 0 ? "−" : ""}{money(Math.abs(net))}</b></span>}
          </div>
          <TabBar id="transfers" value={tab} onChange={setTab} tabs={[["buys", `Buys (${data.buys.length})`], ["sales", `Sales (${data.sales.length})`]]} />
          <List rows={tab === "buys" ? data.buys : data.sales} kind={tab} />
          {data.unknown_fees > 0 && <small className="note" data-testid="transfers-unknown-note">{data.unknown_fees} move{data.unknown_fees > 1 ? "s have" : " has"} no fee in the save, so these totals only count recorded fees. The boxes in the finance bar use the club's own finance figures from the save.</small>}
        </>}
      </DialogContent>
    </Dialog>
  );
};
