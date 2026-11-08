import { useState } from "react";
import { TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { DynamicPotential } from "@/components/awards/DynamicPotential";

const Caps = (data, setData) => (
  <div className="card" style={{ marginBottom: 14 }}>
    <p className="sentence">Change at most <input className="blank mono" type="number" style={{ width: 80 }} value={data.caps.max_players} onChange={(e) => setData({ ...data, caps: { ...data.caps, max_players: Number(e.target.value) } })} data-testid="dp-cap-players" /> players per run,
      and no player by more than <input className="blank mono" type="number" style={{ width: 60 }} value={data.caps.max_pa_change} onChange={(e) => setData({ ...data, caps: { ...data.caps, max_pa_change: Number(e.target.value) } })} data-testid="dp-cap-pa" /> PA per season.</p>
  </div>
);

export default function DynamicPotentialPage() {
  const [tab, setTab] = useState("run");
  return (
    <div data-testid="dp-page">
      <PageHead eyebrow="Review development" title="Dynamic Potential">
        <TabBar id="dp" value={tab} onChange={setTab} tabs={[["run", "Run"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "run" ? <DynamicPotential /> : <RulesTab module="dp" title="Growth and decline rules" extra={Caps} />}
    </div>
  );
}
