import { GaugeIcon, Trash2Icon, Undo2Icon } from "lucide-react";
import { useMemo } from "react";
import {
  AsyncBoundary,
  Box,
  ClassSelect,
  Flex,
  Grid,
  IconButton,
  Section,
  Text,
  TextField,
  Tooltip,
} from "../../components";
import { useClassTaxonomies } from "../../hooks/useClassTaxonomies";
import { classOptions } from "../../lib/classOptions";
import { formatCount } from "../../lib/format";
import type { FlowEditsState } from "./useFlowEdits";

const COLUMNS = "minmax(150px, 1.4fr) minmax(130px, 1fr) 240px minmax(140px, 1fr) 80px 90px 32px";

// The sOCEL's flows, each editable in place: name, unit (converting the
// quantities), category and reference; or deleted with its records.
export default function FlowConfig({ state }: { state: FlowEditsState }) {
  const taxonomies = useClassTaxonomies();
  const categories = useMemo(
    () => classOptions(taxonomies.data?.flowCategories ?? []),
    [taxonomies.data],
  );
  const { inventory } = state;

  return (
    <Section
      icon={GaugeIcon}
      title="Flows"
      aside={
        <Text size="2" color="gray">
          {formatCount(state.flows.length)}
        </Text>
      }
    >
      <AsyncBoundary
        status={inventory}
        isEmpty={(flows) => flows.length === 0}
        loadingLabel="Reading the flows…"
        errorTitle="The flows could not be read"
        emptyState={{ title: "No flows", description: "This sOCEL declares no flows." }}
        onRetry={() => void inventory.refetch()}
      >
        {(flows) => (
          <Box style={{ overflowX: "auto" }}>
            <Box style={{ minWidth: 960 }}>
              <Grid columns={COLUMNS} gap="2" align="center" px="2" pb="2">
                <Label>Flow</Label>
                <Label>Unit</Label>
                <Label>Category</Label>
                <Label>Reference</Label>
                <Label end>Instances</Label>
                <Label end>Records</Label>
                <span />
              </Grid>
              {flows.map((flow) => {
                const draft = state.draftOf(flow);
                const problem = state.problemOf(flow);
                const off = draft.deleted;
                return (
                  <Grid
                    key={flow.flowId}
                    columns={COLUMNS}
                    gap="2"
                    align="start"
                    px="2"
                    py="2"
                    style={{
                      borderTop: "1px solid var(--gray-a4)",
                      background: state.isChanged(flow) && !off ? "var(--accent-a2)" : undefined,
                      opacity: off ? 0.5 : undefined,
                    }}
                  >
                    <TextField.Root
                      aria-label={`Name of ${flow.flowId}`}
                      value={draft.name}
                      disabled={off}
                      color={problem === "name" || problem === "taken" ? "red" : undefined}
                      style={off ? { textDecoration: "line-through" } : undefined}
                      onChange={(event) => state.change(flow, { name: event.target.value })}
                    />
                    <Flex direction="column" gap="1">
                      <TextField.Root
                        aria-label={`Unit of ${flow.flowId}`}
                        value={draft.unit}
                        disabled={off}
                        color={problem === "unit" ? "red" : undefined}
                        onChange={(event) => state.change(flow, { unit: event.target.value })}
                      />
                      {state.unitChanged(flow) && draft.unit.trim() !== "" && !off && (
                        // One of the old unit in the new one: what every quantity is multiplied by.
                        <Flex align="center" gap="1">
                          <Text size="1" color="gray" wrap="nowrap">
                            1 {flow.unit} =
                          </Text>
                          <TextField.Root
                            size="1"
                            inputMode="decimal"
                            aria-label={`${draft.unit} in one ${flow.unit}`}
                            placeholder="?"
                            value={draft.conversion}
                            color={problem === "conversion" ? "red" : undefined}
                            style={{ width: 70 }}
                            onChange={(event) =>
                              state.change(flow, { conversion: event.target.value })
                            }
                          />
                          <Text size="1" color="gray" wrap="nowrap">
                            {draft.unit.trim()}
                          </Text>
                        </Flex>
                      )}
                    </Flex>
                    <ClassSelect
                      label={`Category of ${flow.flowId}`}
                      options={categories}
                      value={draft.category}
                      onChange={(category) => state.change(flow, { category })}
                    />
                    <TextField.Root
                      aria-label={`Reference of ${flow.flowId}`}
                      placeholder="optional"
                      value={draft.externalRef}
                      disabled={off}
                      onChange={(event) => state.change(flow, { externalRef: event.target.value })}
                    />
                    <Count value={flow.instances} />
                    <Count value={flow.intervalRecords + flow.eventRecords} />
                    <Tooltip content={off ? "Keep" : "Delete with its records"}>
                      <IconButton
                        variant="ghost"
                        color="gray"
                        aria-label={off ? `Keep ${flow.flowId}` : `Delete ${flow.flowId}`}
                        onClick={() => state.change(flow, { deleted: !off })}
                      >
                        {off ? <Undo2Icon size={15} /> : <Trash2Icon size={15} />}
                      </IconButton>
                    </Tooltip>
                  </Grid>
                );
              })}
            </Box>
          </Box>
        )}
      </AsyncBoundary>
    </Section>
  );
}

function Label({ children, end }: { children: string; end?: boolean }) {
  return (
    <Text size="1" color="gray" weight="medium" align={end ? "right" : undefined}>
      {children}
    </Text>
  );
}

function Count({ value }: { value: number }) {
  return (
    <Text size="2" color="gray" align="right" mt="1" style={{ fontVariantNumeric: "tabular-nums" }}>
      {formatCount(value)}
    </Text>
  );
}
