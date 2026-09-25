import { Stack, Text } from "@mantine/core";
import { useE2o } from "@ocelescope/api-base";
import { EmptyState, LoadingState, useColorOf } from "@r4pm/components";
import { CardSelector } from "@r4pm/components/ui";
import { useOcelId } from "./internal/useOcelId";
import type { E2ORelation, OcelSource } from "./types";

export type E2ORelationPickerProps = OcelSource & {
  /** The activity whose events the relations start from. */
  activity: string | undefined;
  value: E2ORelation | undefined;
  onChange: (value: E2ORelation | undefined) => void;
  label?: string;
  emptyText?: string;
};

/** One card value per relation. JSON keeps object types and qualifiers with
 * any characters apart. */
const keyOf = (relation: E2ORelation) => JSON.stringify([relation.objectType, relation.qualifier]);

const perEvent = (min: number, max: number) => `${min === max ? min : `${min}–${max}`} per event`;

/**
 * The object types an activity's events relate to, one card per qualifier,
 * with how many objects each event relates to.
 */
export const E2ORelationPicker = ({
  activity,
  value,
  onChange,
  label,
  emptyText,
  ocelId,
  ocelVersion = "filtered",
}: E2ORelationPickerProps) => {
  const id = useOcelId(ocelId);
  const colorOf = useColorOf("objectType");
  const { data, isPending } = useE2o(
    id,
    { source_types: activity ? [activity] : [], ocel_version: ocelVersion, page_size: 500 },
    { query: { enabled: id != null && activity !== undefined } },
  );

  const relations = (data?.response ?? []).filter((relation) => relation.source === activity);

  const content = () => {
    if (activity === undefined) return <EmptyState title="Choose an activity first" />;
    if (isPending) return <LoadingState label="Reading the OCEL…" topBar={false} />;
    if (relations.length === 0)
      return <EmptyState title={emptyText ?? "Events of this activity relate to no objects"} />;

    return (
      <CardSelector
        aria-label={label ?? "Related object type"}
        columns={2}
        value={value ? keyOf(value) : ""}
        onValueChange={(key) => {
          const [objectType, qualifier] = JSON.parse(key) as [string, string];
          onChange({ objectType, qualifier });
        }}
        options={relations.map((relation) => ({
          value: keyOf({ objectType: relation.target, qualifier: relation.qualifier }),
          title: relation.target,
          description: `"${relation.qualifier}" · ${perEvent(relation.min_count, relation.max_count)}`,
          icon: (
            <span
              aria-hidden
              style={{
                display: "block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: colorOf(relation.target),
              }}
            />
          ),
        }))}
      />
    );
  };

  return (
    <Stack gap={4}>
      {label && (
        <Text size="xs" c="dimmed">
          {label}
        </Text>
      )}
      {content()}
    </Stack>
  );
};
