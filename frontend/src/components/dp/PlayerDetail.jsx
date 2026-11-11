import { useGet } from "@/lib/ui";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Signal } from "./Overview";

const Bar = ({ label, v, need, testid }) => (
  <div style={{ margin: "6px 0" }} data-testid={testid}>
    <div style={{ display: "flex", fontSize: 12.5 }}><span style={{ flex: 1 }}>{label}</span><span className="mono">{v ?? "\u2014"}{need ? ` / ${need}` : ""}</span></div>
    <div style={{ height: 4, background: "var(--line)", borderRadius: 3 }}><div style={{ height: 4, borderRadius: 3, width: `${Math.min(100, ((v || 0) / (need || 100)) * 100)}%`, background: "var(--acc)" }} /></div>
  </div>
);

const Step = ({ n, title, children }) => (
  <div style={{ display: "flex", gap: 10, padding: "8px 0", borderTop: "1px solid var(--line)" }}>
    <span className="seed-num">{n}</span><div style={{ flex: 1 }}><b style={{ fontSize: 13.5 }}>{title}</b><div className="note" style={{ margin: 0 }}>{children}</div></div>
  </div>
);

const Record = ({ r }) => {
  const e = r.evidence, s = r.score;
  return (
    <div className="card" style={{ padding: 14 }} data-testid={`dp-record-${r.kind}`}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}><b style={{ flex: 1 }}>{r.kind === "winter" ? "Winter review" : "Season-end review"}</b><Signal r={r} /></div>
      <p className="note" style={{ margin: "4px 0 8px" }}>{r.reason}{r.correction ? ` · ${r.correction}` : ""}</p>
      <Bar label="Competitive minutes" v={e.minutes} testid="dp-detail-minutes" />
      <small>First half {e.h1.toLocaleString()} · second half {e.halves_known ? e.h2.toLocaleString() : "not known yet"} · senior {e.senior_share}%</small>
      <Bar label="Match-rating percentile" v={s.rating_pct} testid="dp-detail-rating" />
      <Bar label="Role-output percentile" v={s.role_pct} testid="dp-detail-role" />
      <Step n={1} title={`Performance Score ${s.score ?? "\u2014"}`}>Compared with {r.group_size} players of the same position and a similar expected level{s.ratings_only ? ". Ratings only: role statistics weren't available" : ""}.</Step>
      <Step n={2} title="Evidence">Used: {s.metrics_used.join(", ") || "none"}.{s.standins.length ? ` Stand-ins: ${s.standins.join("; ")}.` : ""}{s.missing.length ? ` Missing: ${s.missing.join(", ")}.` : ""}</Step>
      <Step n={3} title={`Base result ${r.base == null ? "\u2014" : r.base > 0 ? `+${r.base}` : r.base}`}>{r.tier ? `Tier: ${r.tier}. ` : ""}{r.capped.join("; ")}</Step>
      <Step n={4} title={`Age ${e.age}`}>{r.age_deduction ? `\u2212${r.age_deduction} from growth` : "No age deduction"}{r.after_age != null ? `, leaving +${r.after_age}` : ""}.</Step>
      <Step n={5} title="Taper and limits">{r.taper_reduced ? "The taper reduced this change" : "No taper reduction"}{r.winter_applied ? `. +${r.winter_applied} was already given at winter` : ""}.</Step>
      <Step n={6} title={`Final change ${r.change > 0 ? "+" : ""}${r.change}`}>{{ auto: "Sent to your save", approved: "Approved and sent to your save", needs_review: "Waiting for your review", held: "Held", flag: "Flag only, nothing applied", rejected: "Rejected", none: "No change" }[r.status]}{r.flags.length ? ` (${r.flags.join("; ")})` : ""}.</Step>
      <small style={{ color: "var(--dim)" }}>Settings version {r.settings_version} · revision {r.revision}</small>
    </div>
  );
};

export const PlayerDetail = ({ uid, onClose }) => {
  const { data = [] } = useGet(["dp-record", uid], `/dp/records/${uid}`, undefined, { enabled: !!uid });
  return (
    <Sheet open={!!uid} onOpenChange={(v) => !v && onClose()}>
      <SheetContent className="w-[480px] sm:max-w-[480px] overflow-y-auto" data-testid="dp-detail">
        <SheetHeader><SheetTitle>{data[0]?.name || "Review"}</SheetTitle></SheetHeader>
        <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
          {Object.values(Object.fromEntries(data.map((r) => [r.kind, r]).reverse())).map((r) => <Record key={r.id} r={r} />)}
        </div>
      </SheetContent>
    </Sheet>
  );
};
