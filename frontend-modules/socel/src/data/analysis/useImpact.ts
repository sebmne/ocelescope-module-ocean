import { type ImpactOverviewModel, useGetImpact } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type ImpactOverview = ImpactOverviewModel;

/** The traced flows in kg CO₂e with the saved emission factors; only for an sOCEL. */
export function useImpact(isSocel: boolean) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetImpact(ocelId, undefined, { query: { enabled: enabled && isSocel } });
}
