import { useGetLogClassification } from "../api/socel";
import { useSelectedOcel } from "./useSelectedOcel";

export type { TypeClassification } from "../api/socel";

/** How the selected log's activities and object types are classified now. */
export function useLogClassification() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetLogClassification(ocelId, undefined, { query: { enabled } });
}
