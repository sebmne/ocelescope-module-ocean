import { AllocationSection } from "../features/ocean/allocation";
import { EmissionRuleSection } from "../features/ocean/emissionRules";
import { EmissionsSummary, ObjectEmissions } from "../features/ocean/results";
import { Page } from "../ui";

// OCEAn: the key figures on top, then the steps of the analysis in order.
export default function OceanPage() {
  return (
    <Page title="OCEAn">
      <EmissionsSummary />
      <EmissionRuleSection step={1} />
      <AllocationSection step={2} />
      <ObjectEmissions />
    </Page>
  );
}
