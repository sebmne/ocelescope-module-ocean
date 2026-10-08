import { type FlowModel, useGetFlowInventory } from "../api/socel";
import { useSelectedOcel } from "./useSelectedOcel";

export type Flow = FlowModel;

/** The flows of the selected sOCEL with their counts, over the log and per object
 * type; only for an sOCEL. */
export function useFlowInventory() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowInventory(ocelId, undefined, { query: { enabled } });
}
