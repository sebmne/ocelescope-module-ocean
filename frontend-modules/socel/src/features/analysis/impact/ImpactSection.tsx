import { CloudIcon, CogIcon, PackageIcon, SplitIcon } from "lucide-react";
import type { EmissionFactor } from "../../../data/analysis/useAnalysisSettings";
import { useImpact } from "../../../data/analysis/useImpact";
import { formatCo2e, formatCounted, formatMass, formatShare, massParts } from "../../../lib/format";
import {
  BarTree,
  Box,
  EmptyState,
  Flex,
  Grid,
  Histogram,
  Notice,
  NumberField,
  Section,
  Spinner,
  Stat,
  SubHeading,
  Text,
} from "../../../ui";

// Fewer end units read better as a list than as a distribution.
const HISTOGRAM_FROM = 10;

interface ImpactSectionProps {
  step: number;
  flows: readonly { flowId: string; unit: string }[];
  emissionFactors: readonly EmissionFactor[];
  onEmissionFactorsChange: (factors: EmissionFactor[]) => void;
}

// The traced flows in kg CO₂e, with an emission factor per flow: per activity,
// and as what the end units carry.
export default function ImpactSection({
  step,
  flows,
  emissionFactors,
  onEmissionFactorsChange,
}: ImpactSectionProps) {
  const { data } = useImpact(true);
  const factorOf = new Map(emissionFactors.map((f) => [f.flowId, f.impactPerUnit]));
  const setFactor = (flowId: string, impactPerUnit: number | undefined) =>
    onEmissionFactorsChange([
      ...emissionFactors.filter((f) => f.flowId !== flowId),
      ...(impactPerUnit === undefined ? [] : [{ flowId, impactPerUnit }]),
    ]);

  const co2e = (kg: number | undefined) => {
    const { value, unit } = massParts(kg);
    return { value, unit: unit && `${unit} CO₂e` };
  };
  return (
    <Section step={step} title="Impact">
      <Grid columns={{ initial: "1", sm: "2", md: "3" }} gap="3">
        {flows.map((flow) => (
          <Flex key={flow.flowId} direction="column" gap="1">
            <Text size="2" weight="medium">
              {flow.flowId}
            </Text>
            <NumberField
              aria-label={`Factor of ${flow.flowId}`}
              placeholder="No impact"
              unit={`kg CO₂e/${flow.unit}`}
              value={factorOf.get(flow.flowId)}
              onChange={(value) => setFactor(flow.flowId, value)}
            />
          </Flex>
        ))}
      </Grid>

      {emissionFactors.length === 0 ? (
        <EmptyState icon={CloudIcon} title="No emission factors" />
      ) : !data ? (
        <Flex justify="center" py="6">
          <Spinner size="3" />
        </Flex>
      ) : (
        <>
          <Grid columns={{ initial: "1", sm: "3" }} gap={{ initial: "3", md: "4" }}>
            <Stat
              highlight
              icon={CloudIcon}
              label="Recorded"
              {...co2e(data.recorded)}
              hint={formatCounted(data.flows.length, "flow")}
            />
            <Stat
              icon={CogIcon}
              label="Attributed"
              {...co2e(data.attributed)}
              hint={formatShare(data.attributed, data.recorded)}
            />
            <Stat
              icon={SplitIcon}
              label="Allocated"
              {...co2e(data.allocated)}
              hint={formatShare(data.allocated, data.recorded)}
            />
          </Grid>
          <Grid columns={{ initial: "1", md: "2" }} gap="6">
            <Box>
              <SubHeading icon={CogIcon} title="Activities" />
              {data.activities.length === 0 ? (
                <EmptyState icon={CogIcon} title="No operation reached" />
              ) : (
                <BarTree
                  format={formatCo2e}
                  nodes={data.activities.map((activity) => ({
                    id: activity.activity,
                    label: activity.activity,
                    value: activity.impact,
                    valueHint: formatCounted(activity.operations, "operation"),
                    tone: "accent",
                    children: [],
                  }))}
                />
              )}
            </Box>
            <Box>
              <SubHeading icon={PackageIcon} title="End units" />
              {data.lineageProblem && <Notice tone="error">{data.lineageProblem}</Notice>}
              {data.endUnitCount === 0 ? (
                <EmptyState icon={PackageIcon} title="No lineage in step 3" />
              ) : (
                <Flex direction="column" gap="4">
                  {data.medianFootprintPerKg !== null && (
                    <Stat
                      icon={PackageIcon}
                      label="Median per kg"
                      value={data.medianFootprintPerKg.toLocaleString(undefined, {
                        maximumFractionDigits: 3,
                      })}
                      unit="kg CO₂e/kg"
                      hint={formatCounted(data.endUnitCount, "end unit")}
                    />
                  )}
                  {data.endUnitCount >= HISTOGRAM_FROM ? (
                    <Histogram
                      height={200}
                      bins={data.footprintBins.map((bin) => ({
                        from: bin.lower,
                        to: bin.upper,
                        count: bin.endUnits,
                      }))}
                      formatBound={(value) => value.toFixed(3)}
                      valueLabel="kg CO₂e per kg"
                      countLabel="End units"
                    />
                  ) : (
                    <BarTree
                      format={formatCo2e}
                      nodes={data.endUnits.map((unit) => ({
                        id: unit.objectId,
                        label: `${unit.objectId} · ${unit.objectType}`,
                        value: unit.footprint,
                        valueHint: unit.mass !== null ? `of ${formatMass(unit.mass)}` : undefined,
                        tone: "accent",
                        children: [],
                      }))}
                    />
                  )}
                </Flex>
              )}
            </Box>
          </Grid>
        </>
      )}
    </Section>
  );
}
