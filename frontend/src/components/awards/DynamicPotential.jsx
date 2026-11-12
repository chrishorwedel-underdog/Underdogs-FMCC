import { Loading } from "@/components/Loading";

import { useState } from "react";
import { Switch } from "@/components/ui/switch";
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
      <div style={{ maxHeight: 240, overflowY: "auto", marginTop: 6, paddingRight: 32 }}>
        {shown.map((i) => <div className="row" key={i.name}><div style={{ flex: 1 }}>{i.name}<small>{i.count} players in the save</small></div>
          <Switch checked={on.includes(i.name)} onCheckedChange={(v) => set(v ? [...on, i.name] : on.filter((x) => x !== i.name))} data-testid={`dp-${id}-${i.name.replace(/\s+/g, "-").toLowerCase()}`} /></div>)}
      </div>
    </div>
  );
};

const ReviewList = () => {
  const { data = [] } = useGet("dp-review", "/dp/review");
  return (
    <div className="card" data-testid="dp-review">
      <div className="ttl">Who's included</div><p className="note" style={{ marginTop: 4 }}>Everyone listed here is reviewed at winter and season-end.</p>
      <div style={{ maxHeight: 420, overflowY: "auto" }}>
        {data.map((lg) => <div key={lg.league}><div className="eyebrow" style={{ marginTop: 14 }}>{lg.league}</div>
          {lg.clubs.map((cl) => <div key={cl.club} style={{ marginTop: 8 }}><b style={{ fontSize: 13 }}>{cl.club}</b>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6, paddingLeft: 12 }}>
              {cl.players.map((p) => <span key={p.unique_id} className="chipx" data-testid={`dp-player-${p.unique_id}`}>{p.name}</span>)}
            </div></div>)}</div>)}
      </div>
    </div>
  );
};

export const DynamicPotential = () => {
  const { data } = useGet("dp", "/dp/scope");
  const act = useAct();
  if (!data) return <Loading id="dp-loading" rows={5} label="Loading Dynamic Potential" />;
  const save = (scope) => act(() => api.put("/dp/scope", { scope, expected_version: data.version }), null, ["dp", "dp-review", "rules", "dp-overview"]);
  return (
    <div className="homegrid" data-testid="dp-view">
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <div className="card"><div className="ttl">Applies to</div>
          <div className="row" data-testid="dp-all-row"><div style={{ flex: 1 }}><b>All loaded players</b><small>Every player in every league loaded in your save, your club included</small></div><Switch checked={!!data.scope.all_players} onCheckedChange={(v) => save({ ...data.scope, all_players: v })} data-testid="dp-all-players" /></div>
          {!data.scope.all_players && <div className="row"><div style={{ flex: 1 }}><b>My club</b><small>Every player at your club</small></div><Switch checked={data.scope.my_club} onCheckedChange={(v) => save({ ...data.scope, my_club: v })} data-testid="dp-my-club" /></div>}
          <p className="sent" data-testid="dp-covered-count">Covers <b>{data.covered}</b> players{data.scope.all_players ? ": everyone loaded in the game" : <> in {data.covered_leagues} {data.covered_leagues === 1 ? "league" : "leagues"} and {data.covered_nations} {data.covered_nations === 1 ? "nation" : "nations"}{data.scope.my_club ? ", plus your club" : ""}</>}.</p>
          <p className="note" style={{ marginTop: 6 }}>A player covered by more than one toggle is counted once.</p>
        </div>
        {!data.scope.all_players && <ToggleList id="leagues" title="Leagues" items={data.leagues} on={data.scope.leagues} set={(v) => save({ ...data.scope, leagues: v })} />}
        {!data.scope.all_players && <ToggleList id="nations" title="Nations" items={data.nations} on={data.scope.nations} set={(v) => save({ ...data.scope, nations: v })} />}
      </div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <ReviewList />
      </div>
    </div>
  );
};
