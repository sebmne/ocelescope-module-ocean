import { CircleDotIcon, CogIcon, CornerDownRightIcon, GaugeIcon, SplitIcon } from "lucide-react";
import type { FlowAttribution } from "../../../data/analysis/useAttribution";
import { formatCount, formatCounted, formatQuantity, formatShare } from "../../../lib/format";
import {
  Badge,
  BarTree,
  Box,
  EmptyState,
  Flex,
  Grid,
  Section,
  SplitBar,
  Stat,
  SubHeading,
  SwitchField,
  Text,
} from "../../../ui";

interface AttributionSectionProps {
  step: number;
  flow: FlowAttribution;
  groupMetering: boolean;
  onGroupMeteringChange: (groupMetering: boolean) => void;
}

// How much of the flow was recorded during operations - per activity - and per
// meter how much reached an operation and how much remained.
export default function AttributionSection({
  step,
  flow,
  groupMetering,
  onGroupMeteringChange,
}: AttributionSectionProps) {
  const max = Math.max(...flow.meters.map((meter) => Math.abs(meter.recorded)), 0);
  const operations = flow.activities.reduce((sum, activity) => sum + activity.operations, 0);

  return (
    <Section
      step={step}
      title="Attribution to operations"
      actions={
        <SwitchField
          label="Group metering"
          info="A meter whose nested meters record nothing also reaches the operations of the objects directly within it, as a line meter stands for its machines."
          checked={groupMetering}
          onChange={onGroupMeteringChange}
        />
      }
    >
      <Grid columns={{ initial: "2", md: "4" }} gap={{ initial: "3", md: "4" }}>
        <Stat
          icon={GaugeIcon}
          label="Recorded"
          value={formatQuantity(flow.recorded)}
          unit={flow.unit}
          hint={formatCounted(flow.meters.filter((m) => !m.nested).length, "meter")}
        />
        <Stat
          highlight
          icon={CogIcon}
          label="Attributed"
          value={formatQuantity(flow.attributed)}
          unit={flow.unit}
          hint={formatShare(flow.attributed, flow.recorded)}
        />
        <Stat
          icon={SplitIcon}
          label="Remainder"
          value={formatQuantity(flow.remainder)}
          unit={flow.unit}
          hint={formatShare(flow.remainder, flow.recorded)}
        />
        <Stat
          icon={CircleDotIcon}
          label="Operations reached"
          value={formatCount(operations)}
          hint={formatCounted(flow.activities.length, "activity", "activities")}
        />
      </Grid>
      <Grid columns={{ initial: "1", md: "2" }} gap="6">
        <Box>
          <SubHeading icon={CogIcon} title="Activities" />
          {flow.activities.length === 0 ? (
            <EmptyState icon={CogIcon} title="No operation reached" />
          ) : (
            <BarTree
              format={formatQuantity}
              nodes={flow.activities.map((activity) => ({
                id: activity.activity,
                label: activity.activity,
                value: activity.quantity,
                valueHint: formatCounted(activity.operations, "operation"),
                tone: "accent",
                children: [],
              }))}
            />
          )}
        </Box>
        <Box>
          <SubHeading icon={GaugeIcon} title="Meters" />
          <Flex direction="column" gap="3">
            {flow.meters.map((meter) => (
              <SplitBar
                key={meter.objectId}
                max={max}
                done={meter.attributed}
                rest={meter.remainder}
                format={formatQuantity}
                doneLabel="Attributed"
                restLabel="Remainder"
                label={
                  <Flex align="center" gap="2" asChild>
                    <span>
                      {meter.nested && (
                        <Box asChild style={{ color: "var(--gray-8)" }}>
                          <CornerDownRightIcon size={14} aria-label="Nested in another meter" />
                        </Box>
                      )}
                      <Text weight="medium">{meter.objectId}</Text>
                      <Badge color="gray" variant="soft" size="1">
                        {meter.objectType}
                      </Badge>
                    </span>
                  </Flex>
                }
              />
            ))}
          </Flex>
        </Box>
      </Grid>
    </Section>
  );
}
