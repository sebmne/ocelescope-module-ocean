import { useEventAttributes as useAttributesOfEvents, useE2o } from "@ocelescope/api-base";
import { useMemo } from "react";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

/** A numeric attribute of the log's events: the activities whose events have
 * it, and the object types those activities involve. */
export interface EventAttribute {
  name: string;
  activities: readonly string[];
  objectTypes: readonly string[];
}

// The attributes an sOCEL adds to events itself: no flows.
const OWN = new Set(["socel_class", "socel_end_time"]);
const NUMERIC = new Set(["int", "float"]);

/**
 * The numeric attributes of the selected log's events: what could be flows.
 * Read with Ocelescope's own hooks: the attributes per activity, and which
 * object types each activity involves.
 */
export function useEventAttributes() {
  const { ocelId, enabled } = useSelectedOcel();
  const attributes = useAttributesOfEvents(ocelId, undefined, { query: { enabled } });
  const relations = useE2o(ocelId, { page_size: 1000 }, { query: { enabled } });

  const data = useMemo(() => {
    if (!attributes.data || !relations.data) return undefined;
    const typesOf = new Map<string, Set<string>>();
    for (const { source, target } of relations.data.response) {
      typesOf.set(source, (typesOf.get(source) ?? new Set()).add(target));
    }
    const activitiesOf = new Map<string, string[]>();
    for (const attribute of attributes.data) {
      if (OWN.has(attribute.name) || !NUMERIC.has(attribute.type)) continue;
      activitiesOf.set(attribute.name, [
        ...(activitiesOf.get(attribute.name) ?? []),
        attribute.entity_type,
      ]);
    }
    return [...activitiesOf.entries()]
      .map(([name, activities]): EventAttribute => {
        // First the types every one of its activities involves, then the rest.
        const involved = new Map<string, number>();
        for (const activity of activities) {
          for (const type of typesOf.get(activity) ?? []) {
            involved.set(type, (involved.get(type) ?? 0) + 1);
          }
        }
        return {
          name,
          activities: activities.toSorted(),
          objectTypes: [...involved.entries()]
            .toSorted(([a, inA], [b, inB]) => inB - inA || a.localeCompare(b))
            .map(([type]) => type),
        };
      })
      .toSorted((a, b) => a.name.localeCompare(b.name));
  }, [attributes.data, relations.data]);

  return {
    data,
    isPending: attributes.isPending || relations.isPending,
    isError: attributes.isError || relations.isError,
    error: attributes.error ?? relations.error,
    refetch: () => Promise.all([attributes.refetch(), relations.refetch()]),
  };
}
