const SENTENCES = {
  squad: [
    ["An under-21 player needs", "target_minutes", "minutes a month to develop."],
    ["The Development XI starts at most", "max_youth", "under-21 players,"],
    ["and is never more than", "max_team_drop", "points weaker than the Best XI,"],
    ["and never weakens one position by more than", "max_slot_drop", "points."],
    ["Registration: at most", "max_senior", "senior players (21 and over),"],
    ["including at least", "min_homegrown", "homegrown players."],
  ],
  scouting: [
    ["Rankings weigh role fit at", "w_role", "%,"], ["potential at", "w_potential", "%,"], ["age at", "w_age", "%"], ["and value for money at", "w_value", "%."],
    ["Flag a player as over- or under-performing when his rating is", "over_threshold", "away from what his ability suggests."],
  ],
  reports: [["A player is rising when his ability goes up by at least", "rising", "between reports,"], ["and falling when it changes by", "falling", "or less."]],
  development: [["Without a plan, an under-21 player's monthly target is", "default_target", "minutes."], ["He needs minutes when he plays less than", "needs_pct", "% of his target."]],
};

export const ParamsEditor = ({ module, params, set }) => (
  <div className="card" data-testid={`params-editor-${module}`}>
    {SENTENCES[module].map(([before, key, after]) => (
      <p className="sentence" key={key} style={{ padding: "8px 0" }}>{before}{" "}
        <input className="blank mono" type="number" style={{ width: 72 }} value={params[key]} onChange={(e) => set({ ...params, [key]: Number(e.target.value) })} data-testid={`param-${key}`} />{" "}{after}
      </p>
    ))}
  </div>
);
