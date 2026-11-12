import { Loading } from "@/components/Loading";

import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { Switch } from "@/components/ui/switch";

const span = (d) => (d === 0 ? "today" : d < 31 ? `in ${d} day${d === 1 ? "" : "s"}` : `in ${Math.floor(d / 30.4)} month${Math.floor(d / 30.4) === 1 ? "" : "s"} ${Math.round(d % 30.4)} days`);
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");

export const YouthIntake = () => {
  const { data } = useGet("youth-intake", "/youth-intake");
  const act = useAct();
  if (!data) return <Loading id="youth-loading" rows={4} label="Loading intake dates" />;
  const set = (league, body) => act(() => api.put("/youth-intake", { league, ...body }), null, ["youth-intake"]);
  const on = data.rows.filter((r) => r.on);
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="youth-intake">
      <p className="note">Dates marked "est." are typical Football Manager dates. Check the nation's info screen in your game and type the real date to make it exact. The FMCC bell tells you as soon as a save shows an intake has happened.</p>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }} data-testid="youth-countdowns">
        {on.map((r) => <div className="hchip" key={r.league} data-testid={`youth-countdown-${slug(r.league)}`}><b>{r.league}</b>&nbsp;{span(r.days)}{r.estimated && <small style={{ color: "var(--dim)" }}>&nbsp;· est.</small>}</div>)}
        {!on.length && <p className="note">Switch on a league below to track its intake.</p>}
      </div>
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl" data-testid="youth-calendar">
          <thead><tr><th>Track</th><th>League</th><th>Next intake</th><th>Countdown</th><th>Date in your game (MM-DD)</th></tr></thead>
          <tbody>{data.rows.map((r) => (
            <tr key={r.league} style={{ cursor: "default" }} data-testid={`youth-row-${slug(r.league)}`}>
              <td><Switch checked={r.on} onCheckedChange={(v) => set(r.league, { on: v })} aria-label={`Track ${r.league}`} data-testid={`youth-switch-${slug(r.league)}`} /></td>
              <td><b>{r.league}</b></td><td className="mono">{r.date}{r.estimated && <small style={{ color: "var(--dim)" }}> est.</small>}</td><td>{span(r.days)}</td>
              <td><input className="inp mono" style={{ width: 90, height: 30 }} defaultValue={r.mmdd} pattern="\d{2}-\d{2}" onBlur={(e) => e.target.value !== r.mmdd && /^\d{2}-\d{2}$/.test(e.target.value) && set(r.league, { mmdd: e.target.value })} aria-label={`${r.league} intake date`} data-testid={`youth-date-${slug(r.league)}`} /></td>
            </tr>))}</tbody>
        </table>
      </div>
    </div>
  );
};
