import { type SocelStatusModel, useGetSocelStatus } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type SocelStatus = SocelStatusModel;

/** Whether the selected OCEL is an sOCEL, and what it holds (counts only). */
export function useSocelStatus() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetSocelStatus(ocelId, undefined, { query: { enabled } });
}
