import { AllocationSection } from "../features/allocation";
import { EmissionRuleSection } from "../features/emissionRules";
import { EmissionsSummary, ObjectEmissions } from "../features/results";
import { Page } from "../ui";

export default function EmissionsPage() {
  return (
    <Page
      title="Emission analysis"
      description="Assign CO₂e emissions to the events of the OCEL, then allocate them to the objects they belong to."
    >
      <EmissionsSummary />
      <EmissionRuleSection step={1} />
      <AllocationSection step={2} />
      <ObjectEmissions />
    </Page>
  );
}
