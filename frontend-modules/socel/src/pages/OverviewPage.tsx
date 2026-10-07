import { Page } from "../components";
import ClassesSection from "../features/classes/ClassesSection";
import FlowsSection from "../features/flows/FlowsSection";
import SocelSummary from "../features/summary/SocelSummary";

export default function OverviewPage() {
  return (
    <Page title="sOCEL">
      <SocelSummary />
      <FlowsSection />
      <ClassesSection />
    </Page>
  );
}
