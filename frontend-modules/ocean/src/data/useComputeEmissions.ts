import { useQueryClient } from "@tanstack/react-query";
import {
  type E2OEmissionRuleRequest,
  type EventEmissionRuleRequest,
  getGetEmissionsOverviewQueryKey,
  getGetObjectEmissionsQueryKey,
  useComputeEmissions as useComputeEmissionsMutation,
} from "../api/ocean";
import { type EmissionRuleDraft, isRuleComplete } from "../model/emissionRules";
import { errorMessage } from "./errorMessage";
import { useSelectedOcel } from "./useSelectedOcel";

/**
 * Computes the emissions of the complete rules, then refreshes the overview
 * and the allocation (new emissions discard the old allocation). The result
 * counts only while the rules stay as they were sent.
 */
export function useComputeEmissions(rules: readonly EmissionRuleDraft[]) {
  const { id } = useSelectedOcel();
  const queryClient = useQueryClient();
  const mutation = useComputeEmissionsMutation({
    mutation: {
      onSuccess: async () => {
        if (!id) return;
        await queryClient.invalidateQueries({ queryKey: getGetEmissionsOverviewQueryKey(id) });
        await queryClient.invalidateQueries({ queryKey: getGetObjectEmissionsQueryKey(id) });
      },
    },
  });

  const requests = rules.map(toRequest).filter((rule) => rule !== null);
  const sent = mutation.variables?.ocelId === id ? mutation.variables?.data.rules : undefined;
  const isCurrent = JSON.stringify(sent) === JSON.stringify(requests);

  return {
    compute: () => id && mutation.mutate({ ocelId: id, data: { rules: requests } }),
    canCompute: id !== null && requests.length > 0,
    isPending: mutation.isPending,
    /** The rules changed since they were last computed (in this visit of the page). */
    isOutdated: sent !== undefined && !isCurrent && mutation.isSuccess,
    error: isCurrent ? errorMessage(mutation.error, "Computing emissions failed.") : undefined,
  };
}

/** A draft as the backend expects it, or null while it is incomplete. */
function toRequest(
  rule: EmissionRuleDraft,
): EventEmissionRuleRequest | E2OEmissionRuleRequest | null {
  if (!isRuleComplete(rule) || !rule.activity) return null;

  const factor = {
    valueKg: rule.factor.value ?? 0,
    attributes: rule.factor.attributes.map((ref) =>
      ref.target === "event"
        ? { target: "event" as const, name: ref.name }
        : { target: "object" as const, objectType: ref.objectType, name: ref.name },
    ),
  };

  if (rule.type === "E") return { type: "E", activity: rule.activity, factor };
  if (!rule.relation) return null;
  return {
    type: "E2O",
    activity: rule.activity,
    objectType: rule.relation.objectType,
    qualifier: rule.relation.qualifier || null,
    factor,
  };
}
