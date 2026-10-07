import { Group, Stack, Text } from "@mantine/core";
import {
  useE2o,
  useEventAttributes,
  useObjectAttributes,
  type ValueType,
} from "@ocelescope/api-base";
import {
  EmptyState,
  FrequencyPicker,
  LoadingState,
  softBadgeStyle,
  useColorOf,
} from "@r4pm/components";
import { Badge } from "@r4pm/components/ui";
import { attributeItems } from "./internal/attributeItems";
import { useOcelId } from "./internal/useOcelId";
import type { AttributeRef, OcelSource } from "./types";

export type RelatedAttributePickerProps = OcelSource & {
  /** The activity whose event attributes, and related objects' attributes, are offered. */
  activity: string | undefined;
  /** Offer attributes of only these related object types. Default: all related types. */
  objectTypes?: readonly string[];
  /** Offer only object types every event relates to exactly one object of, so
   * an object attribute has one value per event. */
  onlyUniquelyRelated?: boolean;
  /** Offer only attributes of these value types, e.g. `["int", "float"]`. */
  valueTypes?: readonly ValueType[];
  value: readonly AttributeRef[];
  onChange: (value: AttributeRef[]) => void;
  label?: string;
  emptyText?: string;
};

/**
 * Attributes around an activity: those its events carry, and those of the
 * object types its events relate to, grouped by where they come from.
 */
export const RelatedAttributePicker = ({
  activity,
  objectTypes,
  onlyUniquelyRelated = false,
  valueTypes,
  value,
  onChange,
  label,
  emptyText,
  ocelId,
  ocelVersion = "filtered",
}: RelatedAttributePickerProps) => {
  const id = useOcelId(ocelId);
  const activityColor = useColorOf("activity");
  const objectTypeColor = useColorOf("objectType");
  const enabled = id != null && activity !== undefined;

  const events = useEventAttributes(
    id,
    { ocel_version: ocelVersion, names: activity ? [activity] : [] },
    { query: { enabled } },
  );
  const relations = useE2o(
    id,
    { source_types: activity ? [activity] : [], ocel_version: ocelVersion, page_size: 500 },
    { query: { enabled } },
  );
  const relationRows = relations.data?.response ?? [];
  // Unique: one qualifier, and exactly one object per event.
  const isUnique = (type: string) => {
    const rows = relationRows.filter((relation) => relation.target === type);
    return rows.length === 1 && rows[0].min_count === 1 && rows[0].max_count === 1;
  };
  const relatedTypes = [...new Set(relationRows.map((relation) => relation.target))]
    .filter((type) => !objectTypes || objectTypes.includes(type))
    .filter((type) => !onlyUniquelyRelated || isUnique(type));
  const objects = useObjectAttributes(
    id,
    { ocel_version: ocelVersion, names: relatedTypes },
    { query: { enabled: enabled && relatedTypes.length > 0 } },
  );

  // Every source of attributes, with what is picked from it.
  const groups = [
    {
      key: `event:${activity}`,
      name: activity ?? "",
      color: activityColor(activity ?? ""),
      caption: "event attributes",
      items: attributeItems(events.data, valueTypes),
      picked: value.filter((ref) => ref.target === "event").map((ref) => ref.name),
      toRefs: (names: string[]): AttributeRef[] =>
        names.map((name) => ({ target: "event", activity: activity ?? "", name })),
      isOwn: (ref: AttributeRef) => ref.target === "event",
    },
    ...relatedTypes.map((objectType) => ({
      key: `object:${objectType}`,
      name: objectType,
      color: objectTypeColor(objectType),
      caption: "object attributes",
      items: attributeItems(
        objects.data?.filter((attribute) => attribute.entity_type === objectType),
        valueTypes,
      ),
      picked: value
        .filter((ref) => ref.target === "object" && ref.objectType === objectType)
        .map((ref) => ref.name),
      toRefs: (names: string[]): AttributeRef[] =>
        names.map((name) => ({ target: "object", objectType, name })),
      isOwn: (ref: AttributeRef) => ref.target === "object" && ref.objectType === objectType,
    })),
  ].filter((group) => group.items.length > 0);

  const loading =
    events.isPending || relations.isPending || (relatedTypes.length > 0 && objects.isPending);

  const content = () => {
    if (activity === undefined) return <EmptyState title="Choose an activity first" />;
    if (loading) return <LoadingState label="Reading the OCEL…" topBar={false} />;
    if (groups.length === 0)
      return <EmptyState title={emptyText ?? "No attributes to pick from"} />;

    return groups.map((group) => (
      <Stack key={group.key} gap={4}>
        <Group gap={6}>
          <Badge style={softBadgeStyle(group.color)}>{group.name}</Badge>
          <Text size="xs" c="dimmed">
            {group.caption}
          </Text>
        </Group>
        <FrequencyPicker
          items={group.items}
          mode="multi"
          value={new Set(group.picked)}
          onChange={(next) =>
            onChange([...value.filter((ref) => !group.isOwn(ref)), ...group.toRefs([...next])])
          }
          searchable={group.items.length > 8}
          showBars={false}
          showCutoff={false}
          sort="name"
          scope="attribute"
        />
      </Stack>
    ));
  };

  return (
    <Stack gap="sm">
      {label && (
        <Text size="xs" c="dimmed">
          {label}
        </Text>
      )}
      {content()}
    </Stack>
  );
};
