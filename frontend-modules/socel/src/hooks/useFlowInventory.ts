import { type FlowSummary, useGetFlowInventory } from "../api/socel";
import { useSelectedOcel } from "./useSelectedOcel";

export type Flow = FlowSummary;

/** The flows of the selected sOCEL with their counts, over the log and per object
 * type; only for an sOCEL. */
export function useFlowInventory() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowInventory(ocelId, undefined, { query: { enabled } });
}
