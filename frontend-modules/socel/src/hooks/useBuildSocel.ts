import { getGetOcelsQueryKey } from "@ocelescope/api-base";
import { useCurrentOcel } from "@ocelescope/core";
import { useQueryClient } from "@tanstack/react-query";
import { type BuildSocelRequest, useBuildSocel as useBuildSocelRequest } from "../api/socel";
import { useSelectedOcel } from "./useSelectedOcel";

/** A type's class as the user set it; null takes the class away. */
export type Changes = Readonly<Record<string, string | null>>;

/** What a build takes: the new log's name, the classes that changed, and the
 * flows to add with where their records come from. */
export type Build = BuildSocelRequest;

/**
 * Builds the sOCEL of the selected log as a new log and selects it. Only what
 * the user changed is sent: the rest keeps the classes it has.
 */
export function useBuildSocel() {
  const { ocelId } = useSelectedOcel();
  const { setCurrentOcel } = useCurrentOcel();
  const request = useBuildSocelRequest<Error>();
  const queryClient = useQueryClient();

  const build = (data: Build) =>
    request.mutateAsync({ ocelId, data }).then(async ({ ocelId: built }) => {
      // The app only keeps a selection it finds among its logs: load the list
      // with the new log first.
      await queryClient.refetchQueries({ queryKey: getGetOcelsQueryKey() });
      setCurrentOcel(built);
      return built;
    });

  return { build, isBuilding: request.isPending, error: request.error };
}
