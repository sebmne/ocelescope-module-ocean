import { useGetSocelStatus } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type { SocelStatus } from "../../api/socel";

/** What the selected sOCEL holds, in counts; asked only for an sOCEL. */
export function useSocelStatus() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetSocelStatus(ocelId, undefined, { query: { enabled } });
}
