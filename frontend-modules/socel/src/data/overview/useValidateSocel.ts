import { useMutationState } from "@tanstack/react-query";
import {
  getValidateSocelMutationKey,
  useValidateSocel as useValidateSocelMutation,
  type ValidationResultModel,
} from "../../api/socel";
import { errorMessage } from "../errorMessage";
import { useSelectedOcel } from "../useSelectedOcel";

export type ValidationResult = ValidationResultModel;

/** Validates the selected OCEL against V1–V9; the report is kept as a resource. */
export function useValidateSocel() {
  const { id } = useSelectedOcel();
  const mutation = useValidateSocelMutation();
  return {
    validate: () => id && mutation.mutate({ ocelId: id }),
    isPending: mutation.isPending,
    error: errorMessage(mutation.error, "Validating the sOCEL failed."),
  };
}

/** The last validation of the selected OCEL in this visit of the page. */
export function useLastValidation(): ValidationResult | undefined {
  const { id } = useSelectedOcel();
  const validations = useMutationState({
    filters: { mutationKey: getValidateSocelMutationKey(), status: "success" },
    select: (mutation) => ({
      ocelId: (mutation.state.variables as { ocelId?: string } | undefined)?.ocelId,
      result: mutation.state.data as ValidationResult | undefined,
    }),
  });
  return validations.filter((validation) => validation.ocelId === id).at(-1)?.result;
}
