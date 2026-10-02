import { useGetOcel } from "@ocelescope/api-base";
import { useCurrentOcel } from "@ocelescope/core";

/**
 * The OCEL selected in the app, as the generated query hooks need it, and its
 * name. The module's pages only open on an sOCEL (`requiresExtensions` on their
 * routes), so the selected log is one.
 *
 * No OCEL may be selected yet (id is null). The generated hooks still need a
 * string, so `ocelId` is "" and `enabled` false until an id exists.
 */
export function useSelectedOcel() {
  const { id } = useCurrentOcel();
  const { data: ocel } = useGetOcel(id ?? "", { query: { enabled: id !== null } });
  return { id, ocelId: id ?? "", enabled: id !== null, name: ocel?.name };
}
