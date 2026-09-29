import { type FlowModel, useGetFlowInventory } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type Flow = FlowModel;

/** The flows of the selected sOCEL, each with its flow instances; only for an sOCEL. */
export function useFlowInventory(isSocel: boolean) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowInventory(ocelId, undefined, { query: { enabled: enabled && isSocel } });
}
