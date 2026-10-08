import { GaugeIcon, TimerIcon, UploadIcon, ZapIcon } from "lucide-react";
import { type ReactNode, useRef, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Code,
  Flex,
  Progress,
  Section,
  Text,
  TextField,
  Tooltip,
} from "../../components";
import { formatCount } from "../../lib/format";
import ClassSelect from "./ClassSelect";
import type { ClassOption } from "./classOptions";
import type { FlowDraft, FlowDrafts, FlowInFile, RecordFile, RecordIssue } from "./useRecordFile";

const COLUMNS = ["flow", "object", "quantity", "start_time", "end_time", "event"];
const UNITS = ["kWh", "MWh", "MJ", "kg", "t", "m³", "L", "unit"];

const ISSUES: Record<RecordIssue["kind"], string> = {
  unknown_object: "unknown object",
  unknown_event: "unknown event",
  missing_flow: "no flow",
  missing_object: "no object",
  quantity_not_a_number: "quantity not a number",
  neither_interval_nor_event: "neither interval nor event",
  time_not_readable: "time not readable",
  end_not_after_start: "end not after start",
};
const NAMES_IDS = new Set<RecordIssue["kind"]>(["unknown_object", "unknown_event"]);

interface FlowsCardProps {
  file: RecordFile | undefined;
  flows: FlowDrafts;
  categories: readonly ClassOption[];
  isUploading: boolean;
  error: Error | null;
  onUpload: (file: File) => void;
  onDefine: (flowId: string, change: Partial<FlowDraft>) => void;
}

// The flow records of the sOCEL, taken from one CSV. The file names the flows;
// their unit and category are set here.
export default function FlowsCard({
  file,
  flows,
  categories,
  isUploading,
  error,
  onUpload,
  onDefine,
}: FlowsCardProps) {
  const input = useRef<HTMLInputElement>(null);
  const choose = () => input.current?.click();
  const share = file && file.rows > 0 ? file.usableRows / file.rows : 0;

  return (
    <Section
      icon={GaugeIcon}
      title="Flows"
      aside={
        file && (
          <Flex align="center" gap="3" flexGrow="1" justify="end">
            <Tooltip
              content={`${formatCount(file.usableRows)} of ${formatCount(file.rows)} rows fit the log`}
            >
              <Flex align="center" gap="2">
                <Progress
                  value={share * 100}
                  size="2"
                  color={share < 1 ? "amber" : undefined}
                  style={{ width: 120 }}
                />
                <Text
                  size="2"
                  color="gray"
                  style={{ fontVariantNumeric: "tabular-nums", minWidth: 36 }}
                >
                  {Math.floor(share * 100)}%
                </Text>
              </Flex>
            </Tooltip>
            <Button variant="soft" color="gray" size="1" onClick={choose} loading={isUploading}>
              <UploadIcon size={14} />
              CSV
            </Button>
          </Flex>
        )
      }
    >
      <input
        ref={input}
        type="file"
        accept=".csv,text/csv"
        hidden
        onChange={(event) => {
          const chosen = event.target.files?.[0];
          if (chosen) onUpload(chosen);
          event.target.value = "";
        }}
      />
      {error && (
        <Text size="2" color="red">
          {error.message}
        </Text>
      )}
      {!file ? (
        <DropArea onChoose={choose} onDrop={onUpload} isUploading={isUploading} />
      ) : (
        <Flex direction="column" gap="4">
          <datalist id="socel-units">
            {UNITS.map((unit) => (
              <option key={unit} value={unit} />
            ))}
          </datalist>
          <Flex direction="column" gap="1">
            {file.flows.map((flow) => (
              <FlowRow
                key={flow.flowId}
                flow={flow}
                draft={flows[flow.flowId] ?? { unit: "", category: null }}
                max={Math.max(1, ...file.flows.map((other) => other.rows))}
                categories={categories}
                onDefine={(change) => onDefine(flow.flowId, change)}
              />
            ))}
          </Flex>
          {file.issues.length > 0 && (
            <Flex gap="2" wrap="wrap">
              {file.issues.map((issue) => (
                <Tooltip
                  key={issue.kind}
                  content={`${NAMES_IDS.has(issue.kind) ? "" : "lines "}${issue.examples.join(", ")}${
                    issue.rows > issue.examples.length ? ", …" : ""
                  }`}
                >
                  <Badge color="amber" variant="soft">
                    {formatCount(issue.rows)} × {ISSUES[issue.kind]}
                  </Badge>
                </Tooltip>
              ))}
            </Flex>
          )}
        </Flex>
      )}
    </Section>
  );
}

function FlowRow({
  flow,
  draft,
  max,
  categories,
  onDefine,
}: {
  flow: FlowInFile;
  draft: FlowDraft;
  max: number;
  categories: readonly ClassOption[];
  onDefine: (change: Partial<FlowDraft>) => void;
}) {
  const empty = flow.usableRows === 0;
  return (
    <Flex align="center" gap="3" style={{ opacity: empty ? 0.5 : 1 }}>
      <Box position="relative" flexGrow="1" minWidth="0">
        {/* All rows of the flow in grey, the ones that fit the log on top. */}
        <Bar width={flow.rows / max} background="var(--gray-a2)" />
        <Bar width={flow.usableRows / max} background="var(--gray-a3)" />
        <Flex position="relative" align="center" justify="between" gap="3" px="2" py="2">
          <Text size="2" weight="medium" truncate>
            {flow.flowId}
          </Text>
          <Flex gap="3" flexShrink="0">
            <Count
              icon={<TimerIcon size={13} />}
              label="Interval records"
              value={flow.intervalRecords}
            />
            <Count
              icon={<ZapIcon size={13} />}
              label="Event-linked records"
              value={flow.eventRecords}
            />
          </Flex>
        </Flex>
      </Box>
      <TextField.Root
        aria-label={`Unit of ${flow.flowId}`}
        placeholder="unit"
        list="socel-units"
        value={draft.unit}
        disabled={empty}
        onChange={(event) => onDefine({ unit: event.target.value })}
        style={{ width: 90 }}
      />
      <ClassSelect
        label={`Category of ${flow.flowId}`}
        options={categories}
        value={draft.category}
        onChange={(category) => onDefine({ category })}
      />
    </Flex>
  );
}

function Bar({ width, background }: { width: number; background: string }) {
  return (
    <Box
      position="absolute"
      inset="0"
      style={{ width: `${width * 100}%`, background, borderRadius: "var(--radius-2)" }}
    />
  );
}

function Count({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <Tooltip content={label}>
      <Flex
        align="center"
        gap="1"
        justify="end"
        style={{
          minWidth: 44,
          color: value > 0 ? "var(--gray-12)" : "var(--gray-8)",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {icon}
        <Text size="2">{formatCount(value)}</Text>
      </Flex>
    </Tooltip>
  );
}

// Where the file goes: the columns it needs are all the page says about it.
function DropArea({
  onChoose,
  onDrop,
  isUploading,
}: {
  onChoose: () => void;
  onDrop: (file: File) => void;
  isUploading: boolean;
}) {
  const [over, setOver] = useState(false);
  return (
    <Flex
      direction="column"
      align="center"
      gap="3"
      py="6"
      onDragOver={(event) => {
        event.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setOver(false);
        const dropped = event.dataTransfer.files[0];
        if (dropped) onDrop(dropped);
      }}
      style={{
        border: "1px dashed var(--gray-a7)",
        borderRadius: "var(--radius-3)",
        background: over ? "var(--accent-a2)" : undefined,
      }}
    >
      <Button variant="soft" onClick={onChoose} loading={isUploading}>
        <UploadIcon size={16} />
        CSV
      </Button>
      <Flex gap="1" wrap="wrap" justify="center">
        {COLUMNS.map((column) => (
          <Code key={column} color="gray" variant="soft">
            {column}
          </Code>
        ))}
      </Flex>
    </Flex>
  );
}
