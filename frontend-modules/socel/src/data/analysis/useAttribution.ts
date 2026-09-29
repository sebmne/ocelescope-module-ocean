import { type FlowAttributionModel, useGetAttribution } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type FlowAttribution = FlowAttributionModel;

/** Every flow of the selected sOCEL attributed to operations; only for an sOCEL. */
export function useAttribution(isSocel: boolean) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetAttribution(ocelId, undefined, { query: { enabled: enabled && isSocel } });
}
