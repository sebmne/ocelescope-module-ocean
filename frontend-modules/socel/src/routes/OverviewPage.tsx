import { ClassesSection } from "../features/overview/classes";
import { FlowsSection } from "../features/overview/flows";
import { SocelSummary } from "../features/overview/summary";
import { Page } from "../ui";

export default function OverviewPage() {
  return (
    <Page title="sOCEL">
      <SocelSummary />
      <FlowsSection />
      <ClassesSection />
    </Page>
  );
}
