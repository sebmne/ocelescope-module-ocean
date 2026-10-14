import { ArrowDownToLineIcon, ArrowUpFromLineIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Box, Flex, Grid, Text, TextField } from "../../components";
import { useFlowInventory } from "../../hooks/useFlowInventory";
import { formatAmount } from "../../lib/format";
import { parseFactor } from "./impact";
import type { FactorEntry, Factors } from "./useFactors";
import type { ImpactReport } from "./useImpact";

const COLUMNS = "minmax(140px, 1fr) 300px 300px 100px";

type Direction = "inflow" | "outflow";

// One row per flow: what flows into the objects and out of them, a factor for
// each, and the impact they give.
export default function FactorTable({
  rows,
  total,
  factors,
  onChange,
}: {
  rows: ImpactReport["flows"];
  total: number;
  factors: Factors;
  onChange: (flowId: string, entry: Partial<FactorEntry>) => void;
}) {
  const categories = new Map(
    (useFlowInventory().data ?? []).map((flow) => [flow.flowId, flow.category]),
  );

  return (
    <Box
      role="table"
      aria-label="Factors"
      style={{
        border: "1px solid var(--gray-a5)",
        borderRadius: "var(--radius-4)",
        overflowX: "auto",
      }}
    >
      <Box style={{ minWidth: 840 }}>
        <Grid
          role="row"
          columns={COLUMNS}
          align="center"
          gap="3"
          px="3"
          py="2"
          style={{ background: "var(--gray-a2)" }}
        >
          <HeaderCell>Flow</HeaderCell>
          <HeaderCell icon={<ArrowDownToLineIcon size={14} aria-hidden />}>Into objects</HeaderCell>
          <HeaderCell icon={<ArrowUpFromLineIcon size={14} aria-hidden />}>
            Out of objects
          </HeaderCell>
          <HeaderCell end>kg CO₂e</HeaderCell>
        </Grid>
        {rows.map((row) => {
          const entry = factors[row.flowId];
          const category = categories.get(row.flowId);
          const factorCell = (direction: Direction, amount: number) => (
            <DirectionCell
              flowId={row.flowId}
              direction={direction}
              amount={amount}
              unit={row.unit}
              value={entry?.[direction] ?? ""}
              onChange={(value) => onChange(row.flowId, { [direction]: value })}
            />
          );
          return (
            <Grid
              key={row.flowId}
              role="row"
              columns={COLUMNS}
              align="center"
              gap="3"
              px="3"
              py="2"
              style={{ borderTop: "1px solid var(--gray-a4)" }}
            >
              <Flex direction="column" minWidth="0">
                <Text size="2" weight="medium" truncate>
                  {row.flowId}
                </Text>
                {category && (
                  <Text size="1" color="gray" truncate>
                    {category}
                  </Text>
                )}
              </Flex>
              {factorCell("inflow", row.inflow)}
              {factorCell("outflow", row.outflow)}
              {row.impact === null ? (
                <Text size="2" color="gray" align="right">
                  –
                </Text>
              ) : (
                <Amount value={row.impact} strong />
              )}
            </Grid>
          );
        })}
        <Grid
          role="row"
          columns={COLUMNS}
          align="center"
          gap="3"
          px="3"
          py="2"
          style={{ borderTop: "1px solid var(--gray-a5)", background: "var(--gray-a2)" }}
        >
          <Text size="2" weight="bold">
            Total
          </Text>
          <span />
          <span />
          <Amount value={total} strong />
        </Grid>
      </Box>
    </Box>
  );
}

// What flows in one direction, and its factor; a direction the flow never
// takes has nothing to weigh.
function DirectionCell({
  flowId,
  direction,
  amount,
  unit,
  value,
  onChange,
}: {
  flowId: string;
  direction: Direction;
  amount: number;
  unit: string;
  value: string;
  onChange: (value: string) => void;
}) {
  if (amount === 0) {
    return (
      <Text size="2" color="gray">
        –
      </Text>
    );
  }
  return (
    <Grid columns="96px minmax(0, 1fr)" align="center" gap="2">
      <Amount value={amount} unit={unit} />
      <TextField.Root
        size="1"
        inputMode="decimal"
        aria-label={`Factor of ${flowId} ${direction === "inflow" ? "into" : "out of"} the objects`}
        placeholder="–"
        color={Number.isNaN(parseFactor(value)) ? "red" : undefined}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <TextField.Slot side="right">
          <Text size="1" color="gray" wrap="nowrap">
            kg CO₂e / {unit}
          </Text>
        </TextField.Slot>
      </TextField.Root>
    </Grid>
  );
}

function HeaderCell({
  children,
  icon,
  end,
}: {
  children: ReactNode;
  icon?: ReactNode;
  end?: boolean;
}) {
  return (
    <Flex role="columnheader" justify={end ? "end" : "start"} align="center" gap="2">
      {icon}
      <Text size="2" weight="bold">
        {children}
      </Text>
    </Flex>
  );
}

function Amount({ value, unit, strong }: { value: number; unit?: string; strong?: boolean }) {
  return (
    <Text
      size="2"
      align="right"
      weight={strong ? "medium" : undefined}
      wrap="nowrap"
      style={{ fontVariantNumeric: "tabular-nums" }}
    >
      {formatAmount(value)}
      {unit && <Text color="gray"> {unit}</Text>}
    </Text>
  );
}
