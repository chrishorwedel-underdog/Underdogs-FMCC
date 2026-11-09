import { useState } from "react";
import { TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { Breakout } from "@/components/awards/Breakout";

export default function BreakoutPage() {
  const [tab, setTab] = useState("picks");
  return (
    <div data-testid="breakout-page">
      <PageHead eyebrow="FMCC picks the season's Breakout Player · the winner is awarded a CA bonus" title="Breakout Player">
        <TabBar id="breakout" value={tab} onChange={setTab} tabs={[["picks", "Nominations"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "picks" ? <Breakout /> : <RulesTab module="breakout" title="Categories, criteria and rewards" />}
    </div>
  );
}
