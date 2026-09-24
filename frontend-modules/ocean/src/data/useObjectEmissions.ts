import { type ObjectEmissionsResponse, useGetObjectEmissions } from "../api/ocean";
import type { AllocationConfig } from "../model/allocation";
import { useSelectedOcel } from "./useSelectedOcel";

/** An allocation as the page shows it: how it was made, totals, steps and histogram. */
export type AllocationResult = Omit<ObjectEmissionsResponse, "config"> & {
  config: AllocationConfig;
};

/** The current allocation of the selected OCEL's emissions (null until allocated). */
export function useObjectEmissions() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetObjectEmissions(ocelId, {
    query: { enabled, select: (data) => (data ? toResult(data) : null) },
  });
}

function toResult({ config, ...rest }: ObjectEmissionsResponse): AllocationResult {
  return {
    ...rest,
    config: {
      targetObjectTypes: config.targetObjectTypes,
      rule: config.rule,
      passViaResources: config.passViaResources ?? false,
      passBetweenSameType: config.passBetweenSameType ?? true,
    },
  };
}
