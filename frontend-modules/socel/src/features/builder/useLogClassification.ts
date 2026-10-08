import { type TypeClassificationModel, useGetLogClassification } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type TypeClassification = TypeClassificationModel;

/** How the selected log's activities and object types are classified now. */
export function useLogClassification() {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetLogClassification(ocelId, undefined, { query: { enabled } });
}
