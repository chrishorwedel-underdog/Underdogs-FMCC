import { ExtrasCard } from "@/components/ExtrasCard";
import { PageHead } from "@/lib/ui";

export default function Extras() {
  return (
    <div data-testid="extras-page">
      <PageHead eyebrow="NG_Regens, Real Name Fix and other packs" title="Downloads you need" purpose="Free community packs that make FM look and read the way FMCC expects." />
      <ExtrasCard />
    </div>
  );
}
