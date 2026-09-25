import { useCurrentOcel } from "@ocelescope/core";

/** The OCEL a picker reads: the one it was given, else the selected one. */
export const useOcelId = (ocelId: string | undefined) => ocelId ?? useCurrentOcel().id;
