import { useGetEmissionsOverview } from "../api/ocean";
import { useSelectedOcel } from "./useSelectedOcel";

/** Totals of the emissions computed for the selected OCEL. */
export function useEmissionsOverview() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetEmissionsOverview(ocelId, { query: { enabled } });
}
