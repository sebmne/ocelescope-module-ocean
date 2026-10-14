import { BarChart } from "@ocelescope/core";
import { Box, Flex, Text } from "../../components";
import type { ImpactReport } from "./useImpact";

// Column names are the axis titles.
const IMPACT = "kg CO₂e";

// The impact per period, one stacked bar part per flow with a factor.
export default function ImpactChart({ rows }: { rows: ImpactReport["byPeriod"] }) {
  return (
    <Box style={{ height: 320 }}>
      {rows.length === 0 ? (
        <Flex
          align="center"
          justify="center"
          height="100%"
          style={{ border: "1px dashed var(--gray-a5)", borderRadius: "var(--radius-4)" }}
        >
          <Text size="2" color="gray">
            No factors yet
          </Text>
        </Flex>
      ) : (
        <BarChart
          rows={rows.map((row) => ({ Period: row.start, Flow: row.flowId, [IMPACT]: row.impact }))}
          x="Period"
          y={IMPACT}
          series="Flow"
          stacked
        />
      )}
    </Box>
  );
}
