import { AllocationSection } from "../features/allocation";
import { EmissionRuleSection } from "../features/emissionRules";
import { EmissionsSummary, ObjectEmissions } from "../features/results";
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
