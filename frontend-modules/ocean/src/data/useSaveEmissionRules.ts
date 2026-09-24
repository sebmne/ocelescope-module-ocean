import { useQueryClient } from "@tanstack/react-query";
import {
  getGetEmissionRulesQueryKey,
  useSaveEmissionRules as useSaveEmissionRulesMutation,
} from "../api/ocean";
import type { EmissionRuleDraft } from "../model/emissionRules";
import { draftToApi } from "./emissionRuleDrafts";
import { errorMessage } from "./errorMessage";

/**
 * Saves the rules of an OCEL. The OCEL is passed explicitly: a save delayed
 * while typing must go to the OCEL the rules were edited for, even if another
 * one is selected by then.
 */
export function useSaveEmissionRules() {
  const queryClient = useQueryClient();
  const mutation = useSaveEmissionRulesMutation({
    mutation: {
      // Keep the stored copy current, so coming back to the page shows the saved rules.
      onSuccess: (saved, { ocelId }) =>
        queryClient.setQueryData(getGetEmissionRulesQueryKey(ocelId), saved),
    },
  });

  return {
    save: (ocelId: string, rules: readonly EmissionRuleDraft[]) =>
      mutation.mutate({ ocelId, data: { rules: rules.map(draftToApi) } }),
    isSaving: mutation.isPending,
    error: errorMessage(mutation.error, "Saving the rules failed."),
  };
}
