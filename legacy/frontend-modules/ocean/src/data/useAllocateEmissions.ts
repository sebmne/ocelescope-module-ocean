import { useQueryClient } from "@tanstack/react-query";
import {
  getGetObjectEmissionsQueryKey,
  useAllocateEmissions as useAllocateEmissionsMutation,
} from "../api/ocean";
import type { AllocationConfig } from "../model/allocation";
import { errorMessage } from "./errorMessage";
import { useSelectedOcel } from "./useSelectedOcel";

/** Allocates the computed emissions, then refreshes the allocation result. */
export function useAllocateEmissions() {
  const { id } = useSelectedOcel();
  const queryClient = useQueryClient();
  const mutation = useAllocateEmissionsMutation({
    mutation: {
      onSuccess: () =>
        id && queryClient.invalidateQueries({ queryKey: getGetObjectEmissionsQueryKey(id) }),
    },
  });

  return {
    allocate: (config: AllocationConfig) => id && mutation.mutate({ ocelId: id, data: config }),
    isPending: mutation.isPending,
    error: errorMessage(mutation.error, "Allocating emissions failed."),
  };
}
