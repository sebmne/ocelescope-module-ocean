import { useO2o, useObjectCounts } from "@ocelescope/api-base";
import { useMemo } from "react";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";
import type { TypeRelation } from "./containment";

/** The selected log's object-to-object relations between object types, and
 * how many objects each type has. Read with Ocelescope's own hooks. */
export function useTypeRelations() {
  const { ocelId, enabled } = useSelectedOcel();
  const relations = useO2o(
    ocelId,
    { with_qualifier: true, drop_constant: false, page_size: 1000 },
    { query: { enabled } },
  );
  const counts = useObjectCounts(ocelId, undefined, { query: { enabled } });

  const data = useMemo(
    (): TypeRelation[] =>
      (relations.data?.response ?? []).map((relation) => ({
        source: relation.source,
        target: relation.target,
        qualifier: relation.qualifier,
        pairs: relation.sum,
        mostPerObject: relation.max_count,
      })),
    [relations.data],
  );
  return { relations: data, counts: counts.data ?? {} };
}
