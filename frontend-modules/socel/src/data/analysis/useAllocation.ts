import { type FlowAllocationModel, useGetAllocation } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type FlowAllocation = FlowAllocationModel;

/** Every flow allocated to handling units, and carried down their lineage; only for an sOCEL. */
export function useAllocation(isSocel: boolean) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetAllocation(ocelId, undefined, { query: { enabled: enabled && isSocel } });
}
