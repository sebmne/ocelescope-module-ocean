import { type SocelStatusModel, useGetSocelStatus } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type SocelStatus = SocelStatusModel;

/** What the selected sOCEL holds, in counts; asked only for an sOCEL. */
export function useSocelStatus() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetSocelStatus(ocelId, undefined, { query: { enabled } });
}
