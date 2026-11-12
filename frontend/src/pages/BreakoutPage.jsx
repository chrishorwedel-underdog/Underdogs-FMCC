import { useState } from "react";
import { TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { Breakout } from "@/components/awards/Breakout";

export default function BreakoutPage() {
  const [tab, setTab] = useState("picks");
  return (
    <div data-testid="breakout-page">
      <PageHead eyebrow="Picked and applied automatically at season end" title="Breakout Player">
        <TabBar id="breakout" value={tab} onChange={setTab} tabs={[["picks", "Standings"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "picks" ? <Breakout /> : <RulesTab module="breakout" title="Categories, criteria and rewards" />}
    </div>
  );
}
