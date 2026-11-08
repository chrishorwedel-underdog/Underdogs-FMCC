import { useState } from "react";
import { TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { Breakout } from "@/components/awards/Breakout";
import { DynamicPotential } from "@/components/awards/DynamicPotential";

export default function Awards() {
  const [tab, setTab] = useState("breakout");
  return (
    <div data-testid="awards-page">
      <PageHead eyebrow="Annual Breakout and Dynamic Potential" title="Awards">
        <TabBar id="awards" value={tab} onChange={setTab} tabs={[["breakout", "Annual Breakout"], ["dp", "Dynamic Potential"], ["bo-rules", "Breakout rules"], ["dp-rules", "DP rules"]]} />
      </PageHead>
      {tab === "breakout" && <Breakout />}
      {tab === "dp" && <DynamicPotential />}
      {tab === "bo-rules" && <RulesTab module="breakout" title="Award categories, criteria and rewards" />}
      {tab === "dp-rules" && <RulesTab module="dp" title="Growth and decline rules" extra={(data, setData) => (
        <div className="card" style={{ marginBottom: 14 }}>
          <p className="sentence">Change at most <input className="blank mono" type="number" style={{ width: 80 }} value={data.caps.max_players} onChange={(e) => setData({ ...data, caps: { ...data.caps, max_players: Number(e.target.value) } })} data-testid="dp-cap-players" /> players per run,
            and no player by more than <input className="blank mono" type="number" style={{ width: 60 }} value={data.caps.max_pa_change} onChange={(e) => setData({ ...data, caps: { ...data.caps, max_pa_change: Number(e.target.value) } })} data-testid="dp-cap-pa" /> PA per season.</p>
        </div>)} />}
    </div>
  );
}
