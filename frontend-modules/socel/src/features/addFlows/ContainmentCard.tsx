import { BoxesIcon, PlusIcon, XIcon } from "lucide-react";
import { Box, Button, Flex, Grid, IconButton, Section, Select, Text } from "../../components";
import { formatCount } from "../../lib/format";
import { type ContainmentDraft, nesting, problemOf, type TypeRelation } from "./containment";
import { useTypeRelations } from "./useTypeRelations";

interface ContainmentCardProps {
  /** The flows of the new sOCEL, which the containments can apply to. */
  flows: readonly string[];
  containments: readonly ContainmentDraft[];
  onChange: (containments: ContainmentDraft[]) => void;
}

// Which objects lie inside which, per flow, from the log's object-to-object
// relations: one containment per pair of object types, never a choice per object.
export default function ContainmentCard({ flows, containments, onChange }: ContainmentCardProps) {
  const { relations, counts } = useTypeRelations();
  const set = (containment: ContainmentDraft) =>
    onChange(containments.map((other) => (other.id === containment.id ? containment : other)));
  const add = () =>
    onChange([
      ...containments,
      {
        id: Math.max(0, ...containments.map((containment) => containment.id)) + 1,
        objectType: null,
        parentType: null,
        qualifier: null,
        flows: [],
      },
    ]);
  const pictured = flows.filter((flow) => nesting(containments, flow).length > 0);

  return (
    <Section
      icon={BoxesIcon}
      title="Containment"
      aside={
        <Flex flexGrow="1" justify="end">
          <Button variant="soft" color="gray" size="1" onClick={add}>
            <PlusIcon size={14} />
            Add
          </Button>
        </Flex>
      }
    >
      {containments.length === 0 ? (
        <Text size="2" color="gray">
          Nothing lies inside anything yet.
        </Text>
      ) : (
        <Grid
          columns="150px auto 150px minmax(0, 1.2fr) minmax(0, 1.4fr) 24px"
          gap="2"
          align="center"
        >
          <Label>Object type</Label>
          <span />
          <Label>Object type</Label>
          <Label>By the relation</Label>
          <Label>For the flows</Label>
          <span />
          {containments.map((containment) => (
            <Row
              key={containment.id}
              containment={containment}
              flows={flows}
              relations={relations}
              problem={problemOf(containment, relations, containments)}
              onChange={set}
              onRemove={() => onChange(containments.filter((other) => other.id !== containment.id))}
            />
          ))}
        </Grid>
      )}
      {pictured.length > 0 && (
        <Flex gap="6" wrap="wrap">
          {pictured.map((flow) => (
            <Box key={flow}>
              <Text as="div" size="1" color="gray" mb="1">
                {flow}
              </Text>
              {nesting(containments, flow).map(({ type, depth }) => (
                <Flex key={`${type}-${depth}`} gap="3" style={{ paddingLeft: depth * 18 }}>
                  <Text size="2" style={{ minWidth: 110 }}>
                    {type}
                  </Text>
                  <Text size="2" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
                    {formatCount(counts[type] ?? 0)}
                  </Text>
                </Flex>
              ))}
            </Box>
          ))}
        </Flex>
      )}
    </Section>
  );
}

function Label({ children }: { children: string }) {
  return (
    <Text size="1" color="gray" weight="medium">
      {children}
    </Text>
  );
}

function Row({
  containment,
  flows,
  relations,
  problem,
  onChange,
  onRemove,
}: {
  containment: ContainmentDraft;
  flows: readonly string[];
  relations: readonly TypeRelation[];
  problem: string | null;
  onChange: (containment: ContainmentDraft) => void;
  onRemove: () => void;
}) {
  const sources = [...new Set(relations.map((relation) => relation.source))].toSorted();
  const targets = [
    ...new Set(
      relations
        .filter((relation) => relation.source === containment.objectType)
        .map((relation) => relation.target),
    ),
  ].toSorted();
  const qualifiers = relations.filter(
    (relation) =>
      relation.source === containment.objectType && relation.target === containment.parentType,
  );

  return (
    <>
      <Choose
        label="Object type that lies inside"
        value={containment.objectType}
        options={sources.map((type) => ({ value: type, label: type }))}
        onChange={(objectType) =>
          onChange({ ...containment, objectType, parentType: null, qualifier: null })
        }
      />
      <Text size="2" color="gray">
        inside
      </Text>
      <Choose
        label="Object type around it"
        value={containment.parentType}
        options={targets.map((type) => ({ value: type, label: type }))}
        onChange={(parentType) => onChange({ ...containment, parentType, qualifier: null })}
      />
      <Choose
        label="Relation"
        value={containment.qualifier}
        options={qualifiers.map((relation) => ({
          value: relation.qualifier,
          label: `${relation.qualifier} · ${formatCount(relation.pairs)} pairs`,
        }))}
        onChange={(qualifier) => onChange({ ...containment, qualifier })}
      />
      <Flex gap="1" wrap="wrap">
        {flows.map((flow) => {
          const chosen = containment.flows.includes(flow);
          return (
            <Button
              key={flow}
              size="1"
              variant={chosen ? "soft" : "outline"}
              color={chosen ? undefined : "gray"}
              onClick={() =>
                onChange({
                  ...containment,
                  flows: chosen
                    ? containment.flows.filter((other) => other !== flow)
                    : [...containment.flows, flow],
                })
              }
            >
              {flow}
            </Button>
          );
        })}
      </Flex>
      <IconButton variant="ghost" color="gray" size="1" aria-label="Remove" onClick={onRemove}>
        <XIcon size={14} />
      </IconButton>
      {problem && problem !== "Not filled in" && (
        <Text size="1" color="amber" style={{ gridColumn: "1 / -1" }}>
          {problem}
        </Text>
      )}
    </>
  );
}

// Radix has no empty value: this one stands for nothing chosen yet.
const NONE = "__none__";

function Choose({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string | null;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <Select.Root
      value={value ?? NONE}
      onValueChange={(next) => next !== NONE && onChange(next)}
      disabled={options.length === 0}
    >
      <Select.Trigger aria-label={label} variant={value ? "soft" : "surface"} />
      <Select.Content position="popper">
        <Select.Item value={NONE} disabled>
          –
        </Select.Item>
        {options.map((option) => (
          <Select.Item key={option.value} value={option.value}>
            {option.label}
          </Select.Item>
        ))}
      </Select.Content>
    </Select.Root>
  );
}
