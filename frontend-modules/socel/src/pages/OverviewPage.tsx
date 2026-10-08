import { useState } from "react";
import { Page } from "../components";
import ClassesSection from "../features/classes/ClassesSection";
import FlowInstances from "../features/flowInstances/FlowInstances";
import FlowsSection from "../features/flows/FlowsSection";
import SocelSummary from "../features/summary/SocelSummary";
import { useFlowInventory } from "../hooks/useFlowInventory";

// What the sOCEL holds. Choosing a flow's object type there shows that flow's
// objects instead: a subpage the navigation does not list.
export default function OverviewPage() {
  const [shown, setShown] = useState<{ flowId: string; objectType: string | null }>();
  const flow = useFlowInventory().data?.find((candidate) => candidate.flowId === shown?.flowId);

  if (shown) {
    return (
      <Page
        title={shown.flowId}
        subtitle={flow ? [flow.unit, flow.category].filter(Boolean).join(" · ") : undefined}
        back={{ label: "Overview", onClick: () => setShown(undefined) }}
      >
        <FlowInstances flowId={shown.flowId} initialObjectType={shown.objectType} />
      </Page>
    );
  }

  return (
    <Page title="sOCEL">
      <SocelSummary />
      <FlowsSection onOpen={(flowId, objectType) => setShown({ flowId, objectType })} />
      <ClassesSection />
    </Page>
  );
}
