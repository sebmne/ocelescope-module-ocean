import { getGetOcelsQueryKey } from "@ocelescope/api-base";
import { useCurrentOcel } from "@ocelescope/core";
import { useQueryClient } from "@tanstack/react-query";
import { type RecordsToImportModel, useBuildSocel as useBuildSocelRequest } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

/** An uploaded record file with the unit and category of each of its flows. */
export type RecordsToImport = RecordsToImportModel;

/** A type's class as the user set it; null takes the class away. */
export type Changes = Readonly<Record<string, string | null>>;

/**
 * Builds the sOCEL of the selected log as a new log and selects it. Only what
 * the user changed is sent: the rest keeps the classes it has.
 */
export function useBuildSocel() {
  const { ocelId } = useSelectedOcel();
  const { setCurrentOcel } = useCurrentOcel();
  const request = useBuildSocelRequest<Error>();
  const queryClient = useQueryClient();

  const build = (
    name: string,
    activities: Changes,
    objectTypes: Changes,
    records: RecordsToImport | null,
  ) =>
    request
      .mutateAsync({ ocelId, data: { name, activities, objectTypes, records } })
      .then(async ({ ocelId: built }) => {
        // The app only keeps a selection it finds among its logs: load the list
        // with the new log first.
        await queryClient.refetchQueries({ queryKey: getGetOcelsQueryKey() });
        setCurrentOcel(built);
        return built;
      });

  return { build, isBuilding: request.isPending, error: request.error };
}
