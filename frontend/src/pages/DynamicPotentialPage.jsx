import { useState } from "react";
import { TabBar, PageHead } from "@/lib/ui";
import { DynamicPotential } from "@/components/awards/DynamicPotential";
import { Overview } from "@/components/dp/Overview";
import { NeedsReview } from "@/components/dp/NeedsReview";
import { DPSettings } from "@/components/dp/Settings";
import { BalancePreview } from "@/components/dp/BalancePreview";

const VIEWS = { overview: Overview, review: NeedsReview, preview: BalancePreview, settings: DPSettings, scope: DynamicPotential };

export default function DynamicPotentialPage() {
  const [tab, setTab] = useState("overview");
  const View = VIEWS[tab];
  return (
    <div data-testid="dp-page">
      <PageHead eyebrow="Underdog FM rulesheet · winter and season-end reviews" title="Dynamic Potential">
        <TabBar id="dp" value={tab} onChange={setTab} tabs={[["overview", "Overview"], ["review", "Needs your review"], ["preview", "Balance preview"], ["settings", "Settings"], ["scope", "Who's reviewed"]]} />
      </PageHead>
      <View />
    </div>
  );
}
