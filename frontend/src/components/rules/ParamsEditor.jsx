import { RuleItem } from "@/components/rules/RuleItem";

export const SENTENCES = {
  squad: [
    ["An under-21 player needs", "target_minutes", "minutes a month to develop.", "Used to flag youngsters who aren't playing enough."],
    ["The Development XI starts at most", "max_youth", "under-21 players,", "Keeps the youth-heavy lineup realistic."],
    ["and is never more than", "max_team_drop", "points weaker than the Best XI,", "How much overall strength you'll give up to play youngsters."],
    ["and never weakens one position by more than", "max_slot_drop", "points.", "Stops one position becoming a big weak spot."],
    ["Registration: at most", "max_senior", "senior players (21 and over),", "The squad-registration limit FMCC checks against."],
    ["including at least", "min_homegrown", "homegrown players.", "The homegrown quota FMCC checks against."],
  ],
  scouting: [
    ["Rankings weigh role fit at", "w_role", "%,", "How much a player's fit for the role counts in Scout Players rankings."],
    ["potential at", "w_potential", "%,", "How much room to grow counts. The real potential number is never shown."],
    ["age at", "w_age", "%", "How much being young counts."],
    ["and value for money at", "w_value", "%.", "How much a low price counts."],
    ["Flag a player as over- or under-performing when his rating is", "over_threshold", "away from what his ability suggests.", "A bigger number flags fewer players."],
  ],
  reports: [
    ["A player is rising when his ability goes up by at least", "rising", "between reports,", "Sets who gets the rising arrow in monthly reports."],
    ["and falling when it changes by", "falling", "or less.", "Sets who gets the falling arrow."],
  ],
  development: [
    ["Without a plan, an under-21 player's monthly target is", "default_target", "minutes.", "Used for youngsters you haven't given their own plan."],
    ["He needs minutes when he plays less than", "needs_pct", "% of his target.", "Below this share, he's flagged as needing minutes."],
  ],
};

export const ParamsEditor = ({ module, params, set, doc }) => (
  <div style={{ display: "grid", gap: 12 }} data-testid={`params-editor-${module}`}>
    {SENTENCES[module].map(([before, key, after, help]) => {
      const def = doc.defaults.params[key];
      return (
        <RuleItem key={key} id={key} title={`${before} … ${after}`} help={help} now={params[key]} def={def} changedAt={doc.changed_at?.[key]}
          differs={params[key] !== def} onReset={() => set({ ...params, [key]: def })}>
          <p className="sentence" style={{ padding: "2px 0" }}>{before}{" "}
            <input className="blank mono" type="number" style={{ width: 72 }} value={params[key]} onChange={(e) => set({ ...params, [key]: Number(e.target.value) })} aria-label={before} data-testid={`param-${key}`} />{" "}{after}
          </p>
        </RuleItem>
      );
    })}
  </div>
);
