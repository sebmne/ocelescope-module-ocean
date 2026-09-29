import { ChartColumnIcon } from "lucide-react";
import { useObjectEmissions } from "../../../data/ocean/useObjectEmissions";
import { formatCo2e, formatCount, formatMass } from "../../../lib/format";
import {
  Box,
  EmptyState,
  Grid,
  Heading,
  Histogram,
  Panel,
  type Proportion,
  ProportionBar,
  Section,
  Strong,
  Text,
} from "../../../ui";

// How the allocated emissions are distributed over the target objects, and
// which step of the allocation assigned how much.
export default function ObjectEmissions() {
  const { data } = useObjectEmissions();

  if (!data) {
    return (
      <Section icon={ChartColumnIcon} title="Emissions per object">
        <EmptyState icon={ChartColumnIcon} title="Nothing allocated yet" />
      </Section>
    );
  }

  const bins = data.histogram.map((bin) => ({
    from: bin.lowerKg,
    to: bin.upperKg,
    count: bin.objects,
  }));
  const steps: Proportion[] = [
    {
      label: "Directly",
      value: data.steps.directKg,
      color: "accent",
      description: "Emissions of E2O rules for the target objects themselves.",
    },
    {
      label: "By the allocation rule",
      value: data.steps.ruleKg,
      color: "cyan",
      description: "Event emissions passed on to target objects by the chosen rule.",
    },
    {
      label: "Spread over all targets",
      value: data.steps.fallbackKg,
      color: "amber",
      description:
        "Emissions of events that reach no target object, split evenly over all of them.",
    },
  ];

  return (
    <Section icon={ChartColumnIcon} title="Emissions per object">
      <Grid columns={{ initial: "1", md: "3fr 2fr" }} gap="6">
        <Box>
          <Heading as="h3" size="2" mb="4">
            Distribution
          </Heading>
          {bins.length > 1 ? (
            <Histogram
              bins={bins}
              formatBound={formatMass}
              valueLabel="kg CO₂e per object"
              countLabel="Objects"
            />
          ) : (
            // One bin: every object carries the same, there is nothing to chart.
            <Panel>
              <Text size="2">
                {formatCount(data.targetObjects)} ×{" "}
                <Strong>{formatCo2e(data.totalKg / Math.max(1, data.targetObjects))}</Strong>
              </Text>
            </Panel>
          )}
        </Box>
        <Box>
          <Heading as="h3" size="2" mb="4">
            How it was allocated
          </Heading>
          <ProportionBar parts={steps} format={formatMass} />
        </Box>
      </Grid>
    </Section>
  );
}
