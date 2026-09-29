import { DatabaseIcon } from "lucide-react";
import { useState } from "react";
import { useAnalysisSettings } from "../data/analysis/useAnalysisSettings";
import { useAttribution } from "../data/analysis/useAttribution";
import { useSocelStatus } from "../data/overview/useSocelStatus";
import { AllocationSection } from "../features/analysis/allocation";
import { AttributionSection } from "../features/analysis/attribution";
import { FlowPicker } from "../features/analysis/flows";
import { ImpactSection } from "../features/analysis/impact";
import { FlowSeriesSection } from "../features/analysis/series";
import { parseUtc } from "../lib/format";
import { defaultBucket } from "../model/analysis/buckets";
import { EmptyState, Flex, Notice, Page, Spinner } from "../ui";

// The sOCEL analysis, each step building on the one before: a flow's quantities
// over time, their attribution to operations, their allocation to handling units,
// and their impact. Steps 1-3 show one flow, as units differ; step 4 adds up the
// flows with an emission factor.
export default function AnalysisPage() {
  const status = useSocelStatus().data;
  const isSocel = status?.isSocel ?? false;
  const { data: flows } = useAttribution(isSocel);
  const analysis = useAnalysisSettings();
  const [chosen, setChosen] = useState<string>();

  if (status && !isSocel) {
    return (
      <Page title="Analysis">
        <EmptyState icon={DatabaseIcon} title={`${status.ocelName} is no sOCEL`} />
      </Page>
    );
  }
  const { settings } = analysis;
  if (!status || !flows || !settings) {
    return (
      <Page title="Analysis">
        <Flex justify="center" py="9">
          <Spinner size="3" />
        </Flex>
      </Page>
    );
  }

  const flow = flows.find((candidate) => candidate.flowId === chosen) ?? flows[0];
  const period =
    status.recordsFrom && status.recordsTo
      ? parseUtc(status.recordsTo).getTime() - parseUtc(status.recordsFrom).getTime()
      : undefined;

  return (
    <Page title="Analysis">
      {analysis.error && <Notice tone="error">{analysis.error}</Notice>}
      <FlowPicker flows={flows} value={flow?.flowId} onChange={setChosen} />
      {flow && (
        <>
          <FlowSeriesSection
            key={flow.flowId}
            step={1}
            flow={flow}
            defaultBucket={defaultBucket(period)}
          />
          <AttributionSection
            step={2}
            flow={flow}
            groupMetering={settings.groupMetering}
            onGroupMeteringChange={(groupMetering) => analysis.update({ groupMetering })}
          />
          <AllocationSection
            step={3}
            flowId={flow.flowId}
            createdFromQualifier={settings.createdFromQualifier}
            massAttribute={settings.massAttribute}
            createdFromQualifiers={analysis.createdFromQualifiers}
            massAttributes={analysis.massAttributes}
            onChange={analysis.update}
          />
        </>
      )}
      <ImpactSection
        step={4}
        flows={flows}
        emissionFactors={settings.emissionFactors}
        onEmissionFactorsChange={(emissionFactors) => analysis.update({ emissionFactors })}
      />
    </Page>
  );
}
