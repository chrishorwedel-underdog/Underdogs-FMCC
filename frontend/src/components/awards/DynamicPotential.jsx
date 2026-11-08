import { useState } from "react";
import { EyeOff, Play } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const ToggleList = ({ title, items, on, set, id }) => {
  const [q, setQ] = useState("");
  const shown = items.filter((i) => i.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="card" data-testid={`dp-${id}-list`}>
      <div className="ttl">{title}<span style={{ marginLeft: "auto" }} />
        <button className="btn" onClick={() => set(items.map((i) => i.name))} data-testid={`dp-${id}-all`}>Select all</button><button className="btn" onClick={() => set([])} data-testid={`dp-${id}-clear`}>Clear</button></div>
      <input className="inp" style={{ marginTop: 10 }} placeholder={`Search ${title.toLowerCase()}`} value={q} onChange={(e) => setQ(e.target.value)} />
      <div style={{ maxHeight: 240, overflowY: "auto", marginTop: 6 }}>
        {shown.map((i) => <div className="row" key={i.name}><div style={{ flex: 1 }}>{i.name}<small>{i.count} players in the save</small></div>
          <Switch checked={on.includes(i.name)} onCheckedChange={(v) => set(v ? [...on, i.name] : on.filter((x) => x !== i.name))} data-testid={`dp-${id}-${i.name.replace(/\s+/g, "-").toLowerCase()}`} /></div>)}
      </div>
    </div>
  );
};

const ReviewList = ({ exIds, setExIds, exClubs, setExClubs }) => {
  const { data = [] } = useGet("dp-review", "/dp/review");
  const flip = (arr, set, v) => set(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);
  return (
    <div className="card" data-testid="dp-review">
      <div className="ttl">Review before applying</div><p className="note" style={{ marginTop: 4 }}>Untick players or whole clubs. This list never shows whether a player goes up or down.</p>
      <div style={{ maxHeight: 420, overflowY: "auto" }}>
        {data.map((lg) => <div key={lg.league}><div className="eyebrow" style={{ marginTop: 14 }}>{lg.league}</div>
          {lg.clubs.map((cl) => <div key={cl.club} style={{ marginTop: 8 }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center", fontWeight: 600, fontSize: 13 }}><Checkbox checked={!exClubs.includes(cl.club)} onCheckedChange={() => flip(exClubs, setExClubs, cl.club)} data-testid={`dp-club-${cl.club.replace(/\s+/g, "-").toLowerCase()}`} />{cl.club}</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6, paddingLeft: 24, opacity: exClubs.includes(cl.club) ? 0.4 : 1 }}>
              {cl.players.map((p) => <label key={p.unique_id} className="chipx"><Checkbox checked={!exIds.includes(p.unique_id)} onCheckedChange={() => flip(exIds, setExIds, p.unique_id)} data-testid={`dp-player-${p.unique_id}`} />{p.name}</label>)}
            </div></div>)}</div>)}
      </div>
    </div>
  );
};

export const DynamicPotential = () => {
  const { data } = useGet("dp", "/dp");
  const act = useAct();
  const [review, setReview] = useState(true);
  const [exIds, setExIds] = useState([]);
  const [exClubs, setExClubs] = useState([]);
  if (!data) return <p className="note">Loading Dynamic Potential…</p>;
  const save = (scope) => act(() => api.put("/dp/scope", { scope, expected_version: data.version }), null, ["dp", "dp-review", "rules"]);
  const run = () => act(() => api.post("/dp/run", { exclude_ids: exIds, exclude_clubs: exClubs }), (d) => d.summary, ["dp", "changes", "home"]);
  return (
    <div className="homegrid" data-testid="dp-view">
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <div className="card"><div className="ttl">Applies to</div>
          <div className="row"><div style={{ flex: 1 }}><b>My club</b><small>Every player at your club</small></div><Switch checked={data.scope.my_club} onCheckedChange={(v) => save({ ...data.scope, my_club: v })} data-testid="dp-my-club" /></div>
          <p className="sent" data-testid="dp-covered-count">Covers <b>{data.covered}</b> players in {data.covered_leagues} {data.covered_leagues === 1 ? "league" : "leagues"} and {data.covered_nations} {data.covered_nations === 1 ? "nation" : "nations"}{data.scope.my_club ? ", plus your club" : ""}.</p>
          <p className="note" style={{ marginTop: 6 }}>A player covered by more than one toggle is counted once. Caps: {data.caps.max_players} players, ±{data.caps.max_pa_change} PA per player per season (edit in Rules).</p>
        </div>
        <ToggleList id="leagues" title="Leagues" items={data.leagues} on={data.scope.leagues} set={(v) => save({ ...data.scope, leagues: v })} />
        <ToggleList id="nations" title="Nations" items={data.nations} on={data.scope.nations} set={(v) => save({ ...data.scope, nations: v })} />
      </div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <div className="card"><div className="ttl"><EyeOff size={15} />Run Dynamic Potential</div>
          <p className="note" style={{ marginTop: 6 }}>Changes stay hidden: FMCC never shows who goes up or down, or by how much. You find out by playing FM.</p>
          <div className="row"><div style={{ flex: 1 }}>Review before applying</div><Switch checked={review} onCheckedChange={setReview} data-testid="dp-review-toggle" /></div>
          <button className="btn btn-p btn-l" style={{ marginTop: 10 }} onClick={run} disabled={!data.covered} data-testid="dp-run-button"><Play size={14} />Queue for {data.covered - exIds.length} players</button>
          {data.runs.map((r) => <div className="row" key={r.id}><small style={{ margin: 0 }}>{r.detail}</small></div>)}
        </div>
        {review && <ReviewList exIds={exIds} setExIds={setExIds} exClubs={exClubs} setExClubs={setExClubs} />}
      </div>
    </div>
  );
};
