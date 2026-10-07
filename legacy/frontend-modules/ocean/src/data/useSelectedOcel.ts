import { useCurrentOcel } from "@ocelescope/core";

/**
 * The OCEL selected in the app, as the generated query hooks need it.
 *
 * No OCEL may be selected yet (id is null). The generated hooks still need a
 * string, so `ocelId` is "" and `enabled` false until an id exists.
 */
export function useSelectedOcel() {
  const { id } = useCurrentOcel();
  return { id, ocelId: id ?? "", enabled: id !== null };
}
