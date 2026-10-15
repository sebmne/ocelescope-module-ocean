import { useQueryClient } from "@tanstack/react-query";
import {
  type PreparationDraft,
  useConfigureSocel as useConfigureSocelRequest,
} from "../api/socel";
import { useSelectedOcel } from "./useSelectedOcel";

/**
 * Changes the selected sOCEL in place: it keeps its id and name, and what the
 * app exports is the changed log. Only what the user changed is sent: the rest
 * keeps what it has.
 */
export function useConfigureSocel() {
  const { ocelId } = useSelectedOcel();
  const request = useConfigureSocelRequest<Error>();
  const queryClient = useQueryClient();

  const configure = (data: PreparationDraft) =>
    request.mutateAsync({ ocelId, data }).then(() =>
      // Everything asked of the log so far was asked of the old one.
      queryClient.invalidateQueries(),
    );

  return { configure, isSaving: request.isPending, error: request.error };
}
