import { BoxIcon, PackageIcon } from "lucide-react";
import { useAllocation } from "../../../data/analysis/useAllocation";
import type { SettingChoice } from "../../../data/analysis/useAnalysisSettings";
import { formatCount, formatCounted, formatQuantity } from "../../../lib/format";
import {
  BarTree,
  Box,
  EmptyState,
  Field,
  Flex,
  Grid,
  Notice,
  ProportionBar,
  Section,
  Select,
  Spinner,
  SubHeading,
  Text,
} from "../../../ui";

const NONE = "__none__";

interface AllocationSectionProps {
  step: number;
  flowId: string;
  createdFromQualifier: string | null;
  massAttribute: string | null;
  createdFromQualifiers: readonly SettingChoice[];
  massAttributes: readonly SettingChoice[];
  onChange: (changes: {
    createdFromQualifier?: string | null;
    massAttribute?: string | null;
  }) => void;
}

// The attributed quantities divided among the handling units each operation
// involves and, with a lineage, carried down to the end units.
export default function AllocationSection({
  step,
  flowId,
  createdFromQualifier,
  massAttribute,
  createdFromQualifiers,
  massAttributes,
  onChange,
}: AllocationSectionProps) {
  const { data } = useAllocation(true);
  const flow = data?.flows.find((candidate) => candidate.flowId === flowId);

  return (
    <Section step={step} title="Allocation to handling units">
      <Grid columns={{ initial: "1", sm: "2" }} gap="4">
        <Field
          label="Created from"
          info="The O2O relation by which a handling unit is created from another: its source from its target. A unit passes what it carries on to its children, by their share of the mass."
        >
          <SettingSelect
            value={createdFromQualifier}
            choices={createdFromQualifiers}
            unit="relation"
            onChange={(value) => onChange({ createdFromQualifier: value })}
          />
        </Field>
        <Field label="Mass" info="The handling units' mass at creation, their allocation key.">
          <SettingSelect
            value={massAttribute}
            choices={massAttributes}
            unit="unit"
            onChange={(value) => onChange({ massAttribute: value })}
          />
        </Field>
      </Grid>

      {!data || !flow ? (
        <Flex justify="center" py="6">
          <Spinner size="3" />
        </Flex>
      ) : (
        <>
          {data.lineageProblem && <Notice tone="error">{data.lineageProblem}</Notice>}
          <ProportionBar
            format={(value) => `${formatQuantity(value)} ${flow.unit}`}
            parts={[
              {
                label: "Allocated",
                value: Math.abs(flow.allocated),
                color: "accent",
                description: "Divided equally among the handling units of each operation.",
              },
              {
                label: "Unallocated",
                value: Math.abs(flow.unallocated),
                color: "amber",
                description:
                  "Not attributed to an operation, or attributed to one without a handling unit.",
              },
            ]}
          />
          <Box>
            <SubHeading
              icon={data.hasLineage ? PackageIcon : BoxIcon}
              title={data.hasLineage ? "Carried by end units" : "Allocated to handling units"}
            />
            {flow.units.length === 0 ? (
              <EmptyState icon={BoxIcon} title="Nothing allocated" />
            ) : (
              <>
                <BarTree
                  format={formatQuantity}
                  nodes={flow.units.map((unit) => ({
                    id: unit.objectId,
                    label: `${unit.objectId} · ${unit.objectType}`,
                    value: unit.carried ?? unit.allocated,
                    valueHint:
                      unit.carried !== null
                        ? `${formatQuantity(unit.allocated)} allocated directly`
                        : undefined,
                    tone: "accent",
                    children: [],
                  }))}
                />
                {flow.unitCount > flow.units.length && (
                  <Text as="p" size="1" color="gray" mt="2">
                    {formatCount(flow.units.length)} of {formatCounted(flow.unitCount, "unit")}
                  </Text>
                )}
              </>
            )}
          </Box>
        </>
      )}
    </Section>
  );
}

function SettingSelect({
  value,
  choices,
  unit,
  onChange,
}: {
  value: string | null;
  choices: readonly SettingChoice[];
  unit: string;
  onChange: (value: string | null) => void;
}) {
  return (
    <Select.Root
      value={value ?? NONE}
      onValueChange={(next) => onChange(next === NONE ? null : next)}
    >
      <Select.Trigger style={{ width: "100%" }} />
      <Select.Content>
        <Select.Item value={NONE}>None</Select.Item>
        {choices.map((choice) => (
          <Select.Item key={choice.name} value={choice.name}>
            {choice.name} · {formatCounted(choice.count, unit)}
          </Select.Item>
        ))}
      </Select.Content>
    </Select.Root>
  );
}
