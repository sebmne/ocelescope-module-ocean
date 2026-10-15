import { useGetClassCounts } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type { ClassCount } from "../../api/socel";

/** How many objects and events of the selected OCEL carry each socel_class. */
export function useClassCounts() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetClassCounts(ocelId, undefined, { query: { enabled } });
}
