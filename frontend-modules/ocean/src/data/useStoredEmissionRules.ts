import { useGetEmissionRules } from "../api/ocean";
import { draftFromApi } from "./emissionRuleDrafts";
import { useSelectedOcel } from "./useSelectedOcel";

/**
 * The rules stored for the selected OCEL, as the editor holds them. Read once
 * per OCEL: afterwards the editor owns them and saves its changes back.
 */
export function useStoredEmissionRules() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetEmissionRules(ocelId, {
    query: {
      enabled,
      staleTime: Number.POSITIVE_INFINITY,
      refetchOnWindowFocus: false,
      select: (rules) => rules.map(draftFromApi),
    },
  });
}
