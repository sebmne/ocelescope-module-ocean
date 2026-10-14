import { GaugeIcon } from "lucide-react";
import { ClassSelect, Flex, Grid, Section, Text, TextField } from "../../components";
import type { ClassOption } from "../../lib/classOptions";
import { formatCount } from "../../lib/format";
import { EMPTY_DRAFT, type FlowDraft, type FlowDrafts, type NewFlow } from "./flowDrafts";

const UNITS = ["kWh", "MWh", "MJ", "kg", "t", "m³", "L", "unit"];

interface FlowTableProps {
  flows: readonly NewFlow[];
  drafts: FlowDrafts;
  categories: readonly ClassOption[];
  onDefine: (flowId: string, draft: FlowDraft) => void;
}

// The flows the new sOCEL gets, from the file and from attributes together.
// Neither knows a flow's unit and category: they are set here.
export default function FlowTable({ flows, drafts, categories, onDefine }: FlowTableProps) {
  return (
    <Section
      icon={GaugeIcon}
      title="Flows of the new sOCEL"
      aside={
        <Text size="2" color="gray">
          {formatCount(flows.length)}
        </Text>
      }
    >
      {flows.length === 0 ? (
        <Text size="2" color="gray">
          None yet. Add a file or choose attributes above; an sOCEL can also be created without
          flows.
        </Text>
      ) : (
        <Grid columns="minmax(0, 1fr) 200px 90px 240px 200px" gap="2" align="center">
          <datalist id="socel-units">
            {UNITS.map((unit) => (
              <option key={unit} value={unit} />
            ))}
          </datalist>
          <Label>Flow</Label>
          <Label>Records</Label>
          <Label>Unit</Label>
          <Label>Category</Label>
          <Label>Reference</Label>
          {flows.map((flow) => {
            const draft: FlowDraft = drafts[flow.flowId] ?? EMPTY_DRAFT;
            return (
              <Flex key={flow.flowId} style={{ display: "contents" }}>
                <Flex direction="column" minWidth="0">
                  <Text size="2" weight="medium" truncate>
                    {flow.flowId}
                  </Text>
                  <Text size="1" color="gray" truncate>
                    {[flow.fromFile && "file", ...flow.attributes].filter(Boolean).join(" · ")}
                  </Text>
                </Flex>
                <Text size="2" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {[
                    flow.intervalRecords > 0 && `${formatCount(flow.intervalRecords)} interval`,
                    flow.eventRecords > 0 && `${formatCount(flow.eventRecords)} at events`,
                    flow.attributes.length > 0 && "one per event with a value",
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </Text>
                <TextField.Root
                  aria-label={`Unit of ${flow.flowId}`}
                  placeholder="unit"
                  list="socel-units"
                  value={draft.unit}
                  onChange={(event) =>
                    onDefine(flow.flowId, { ...draft, unit: event.target.value })
                  }
                />
                <ClassSelect
                  label={`Category of ${flow.flowId}`}
                  options={categories}
                  value={draft.category}
                  onChange={(category) => onDefine(flow.flowId, { ...draft, category })}
                />
                <TextField.Root
                  aria-label={`Reference of ${flow.flowId}`}
                  placeholder="optional"
                  value={draft.externalRef}
                  onChange={(event) =>
                    onDefine(flow.flowId, { ...draft, externalRef: event.target.value })
                  }
                />
              </Flex>
            );
          })}
        </Grid>
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
