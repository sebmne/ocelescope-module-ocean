import { useSocelStatus } from "../data/overview/useSocelStatus";
import { ClassesSection } from "../features/overview/classes";
import { FlowsSection } from "../features/overview/flows";
import { SocelSummary } from "../features/overview/summary";
import { ValidationSection } from "../features/overview/validation";
import { Page } from "../ui";

// The sOCEL overview, like Ocelescope's log overview: what the selected sOCEL
// holds - key figures, flows and their metering scopes, classes - and whether it
// conforms. Computations over the records belong to the analysis.
export default function OverviewPage() {
  const isSocel = useSocelStatus().data?.isSocel ?? false;
  return (
    <Page title="sOCEL">
      <SocelSummary />
      {isSocel && (
        <>
          <FlowsSection />
          <ClassesSection />
          <ValidationSection />
        </>
      )}
    </Page>
  );
}
