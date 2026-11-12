import { useGet } from "@/lib/ui";
import { RadarCard, AttrHeatmap, MetricHeatmap, attributeRadar } from "@/components/charts/DataHub";
import { Empty } from "@/components/Empty";

// Radar and heatmap views for one of your own players, from the same scouting data as Scout Players.
export const SquadRadars = ({ uid }) => {
  const { data: p, isError } = useGet("scout-player", `/scout/player/${uid}`, { view: "full", uid }, { enabled: !!uid });
  if (isError) return <Empty id="player-sheet-radar-missing" reason="missing" text="This player isn't in the scouting data yet. Read a newer save to add him." />;
  if (!p) return <p className="note">Loading charts…</p>;
  const pct = (p.profile_keys || []).filter((k) => p.pct?.[k] != null);
  const phases = Object.entries(p.phases || {});
  return (
    <div style={{ display: "grid", gap: 12, marginTop: 20, gridTemplateColumns: "minmax(0,1fr)" }} data-testid="player-sheet-radars">
      {phases.length >= 3 && <RadarCard id="player-sheet-phases-radar" title="Phases of play (percentile)" data={phases.map(([k, v]) => ({ axis: k.replace(/^\w/, (c) => c.toUpperCase()), value: v ?? 0 }))} height={220} />}
      {pct.length > 0
        ? <MetricHeatmap id="player-sheet-metric-heatmap" title="Key stats heatmap (percentile vs his position)" rows={[{ name: p.name, values: Object.fromEntries(pct.map((k) => [k, p.pct[k]])) }]} cols={pct} label={p.labels} />
        : <Empty id="player-sheet-empty-pct" reason="minutes" text={`He has ${p.minutes} minutes. Percentiles need more game time; check back after a few more matches.`} />}
      {p.attributes && <>
        <RadarCard id="player-sheet-attr-radar" title="Attributes by area" data={attributeRadar(p.attributes)} max={20} height={220} />
        <AttrHeatmap id="player-sheet-attr-heat" title="Attributes" attrs={p.attributes} />
      </>}
    </div>
  );
};
