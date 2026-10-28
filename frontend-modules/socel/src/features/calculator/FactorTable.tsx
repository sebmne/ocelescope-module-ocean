
import { ArrowDownToLineIcon, ArrowUpFromLineIcon } from "lucide-react";
import { Table } from "../../components";
import { Box, Flex, Text, TextField } from "../../components";
import { useFlowInventory } from "../../hooks/useFlowInventory";
import { formatAmount } from "../../lib/format";
import { parseFactor } from "./impact";
import type { FactorEntry, Factors } from "./useFactors";
import type { ImpactReport } from "./useImpact";

type Direction = "inflow" | "outflow";

const DIRECTIONS: Direction[] = ["inflow", "outflow"];

type Props = {
  rows: ImpactReport["flows"];
  total: number;
  factors: Factors;
  onChange: (flowId: string, entry: Partial<FactorEntry>) => void;
};

export default function FactorTable({
  rows,
  total,
  factors,
  onChange,
}: Props) {
  const categories = new Map(
    (useFlowInventory().data ?? []).map((flow) => [
      flow.flowId,
      flow.category,
    ]),
  );

  return (
    <Box
      style={{
        overflowX: "auto",
        border: "1px solid var(--gray-a5)",
        borderRadius: "var(--radius-4)",
      }}
    >
      <Table.Root variant="surface" layout="auto" style={{ width: "100%" }}>
        <Table.Header>

          <Table.Row>
            <Table.ColumnHeaderCell rowSpan={2}>
              Flow
            </Table.ColumnHeaderCell>

            <Table.ColumnHeaderCell
              colSpan={2}
              justify="center"
              style={{ boxShadow: "none" }}
            >
              <Flex align="center" justify="center" gap="2">
                <ArrowDownToLineIcon size={14} aria-hidden />
                Into objects
              </Flex>
            </Table.ColumnHeaderCell>

            <Table.ColumnHeaderCell
              colSpan={2}
              justify="center"
              style={{ boxShadow: "none" }}
            >
              <Flex align="center" justify="center" gap="2">
                <ArrowUpFromLineIcon size={14} aria-hidden />
                Out of objects
              </Flex>
            </Table.ColumnHeaderCell>

            <Table.ColumnHeaderCell rowSpan={2} justify="end">
              kg CO₂e
            </Table.ColumnHeaderCell>
          </Table.Row>


          <Table.Row>
            <Table.ColumnHeaderCell justify="end">
              Quantity
            </Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>
              Factor
            </Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell justify="end">
              Quantity
            </Table.ColumnHeaderCell>
            <Table.ColumnHeaderCell>
              Factor
            </Table.ColumnHeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          {rows.map((row) => (
            <Table.Row key={row.flowId}>
              <Table.RowHeaderCell>
                <Flex direction="column" gap="1">
                  <Text size="2" weight="medium">
                    {row.flowId}
                  </Text>
                  {categories.get(row.flowId) && (
                    <Text size="1" color="gray">
                      {categories.get(row.flowId)}
                    </Text>
                  )}
                </Flex>
              </Table.RowHeaderCell>

              {DIRECTIONS.map((direction) => (
                <DirectionCells
                  key={direction}
                  flowId={row.flowId}
                  direction={direction}
                  amount={row[direction]}
                  unit={row.unit}
                  value={factors[row.flowId]?.[direction] ?? ""}
                  onChange={(value) =>
                    onChange(row.flowId, { [direction]: value })
                  }
                />
              ))}

              <Table.Cell justify="end">
                {row.impact === null ? (
                  <Text size="2" color="gray">–</Text>
                ) : (
                  <Amount value={row.impact} strong />
                )}
              </Table.Cell>
            </Table.Row>
          ))}

          <Table.Row style={{ background: "var(--gray-a2)" }}>
            <Table.RowHeaderCell>
              <Text weight="bold">Total</Text>
            </Table.RowHeaderCell>
            <Table.Cell colSpan={4} />
            <Table.Cell justify="end">
              <Amount value={total} strong />
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table.Root>
    </Box>
  );
}

function DirectionCells({
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
      <>
        <Table.Cell></Table.Cell>
        <Table.Cell></Table.Cell>
      </>
    );
  }

  return (
    <>
      <Table.Cell justify="end">
        <Amount value={amount} unit={unit} />
      </Table.Cell>

      <Table.Cell>
        <TextField.Root
          size="1"
          inputMode="decimal"
          aria-label={`Factor of ${flowId} ${
            direction === "inflow" ? "into" : "out of"
          } the objects`}
          placeholder="–"
          color={Number.isNaN(parseFactor(value)) ? "red" : undefined}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          style={{ minWidth: "max-content" }}
        >
          <TextField.Slot side="right">
            <Text size="1" color="gray" wrap="nowrap">
              kg CO₂e / {unit}
            </Text>
          </TextField.Slot>
        </TextField.Root>
      </Table.Cell>
    </>
  );
}

function Amount({
  value,
  unit,
  strong,
}: {
  value: number;
  unit?: string;
  strong?: boolean;
}) {
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
