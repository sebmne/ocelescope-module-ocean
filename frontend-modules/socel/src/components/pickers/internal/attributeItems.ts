import type { TypedAttribute, ValueType } from "@ocelescope/api-base";
import type { NameItem } from "../NamePicker";

/**
 * Attributes as picker items: one per name, counted by distinct values.
 *
 * Without a type filter the endpoint returns an attribute once per entity type
 * that carries it, so "status" on two object types would be listed twice.
 */
export const attributeItems = (
  attributes: readonly TypedAttribute[] | undefined,
  valueTypes?: readonly ValueType[],
): NameItem[] => {
  const distinct = new Map<string, number>();
  for (const attribute of attributes ?? []) {
    if (valueTypes && !valueTypes.includes(attribute.type)) continue;
    distinct.set(
      attribute.name,
      Math.max(distinct.get(attribute.name) ?? 0, attribute.distinct_values),
    );
  }
  return [...distinct].map(([key, count]) => ({ key, count }));
};
