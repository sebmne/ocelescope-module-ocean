import { FileSpreadsheetIcon, Settings2Icon, XIcon } from "lucide-react";
import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Dialog,
  Flex,
  IconButton,
  Section,
  SmallChoice,
  Text,
} from "../../components";
import { formatCount } from "../../lib/format";
import type { Mapping, Preview, RecordFile, RecordIssue, Role } from "./useRecordFile";

const ROLES: readonly { value: Role; label: string }[] = [
  { value: "flow", label: "Flow" },
  { value: "object", label: "Object" },
  { value: "quantity", label: "Quantity" },
  { value: "startTime", label: "Start" },
  { value: "endTime", label: "End" },
  { value: "event", label: "Event" },
];
const UNUSED = "";
const CHOICES = [{ value: UNUSED, label: "Not used" }, ...ROLES];

const ISSUES: Record<RecordIssue["kind"], string> = {
  unknown_object: "unknown object",
  unknown_event: "unknown event",
  missing_flow: "no flow",
  missing_object: "no object",
  quantity_not_a_number: "quantity not a number",
  neither_interval_nor_event: "neither interval nor event",
  time_not_readable: "time not readable",
  end_not_after_start: "end not after start",
  event_end_not_after_start: "event ends before it starts",
  conflicting_event_end: "event with two different ends",
};
// The columns a reason points at; none for a reason that is about the whole row.
const ISSUE_ROLES: Record<RecordIssue["kind"], readonly Role[]> = {
  unknown_object: ["object"],
  missing_object: ["object"],
  missing_flow: ["flow"],
  quantity_not_a_number: ["quantity"],
  unknown_event: ["event"],
  event_end_not_after_start: ["endTime"],
  conflicting_event_end: ["endTime"],
  time_not_readable: ["startTime", "endTime"],
  end_not_after_start: ["startTime", "endTime"],
  neither_interval_nor_event: [],
};

interface FileFlowsProps {
  file: RecordFile;
  name: string | undefined;
  mapping: Mapping;
  preview: Preview | null;
  isReading: boolean;
  error: Error | null;
  /** Whether the popup is open when the card first shows, as after an upload. */
  initiallyOpen?: boolean;
  onAssign: (column: string, role: Role | null) => void;
  onRemove: () => void;
}

// Flow records from a CSV. The file's columns are set up in a popup that shows
// its first rows; the card keeps a summary.
export default function FileFlows({
  file,
  name,
  mapping,
  preview,
  isReading,
  error,
  initiallyOpen = false,
  onAssign,
  onRemove,
}: FileFlowsProps) {
  const [opened, setOpened] = useState(initiallyOpen);

  return (
    <Section
      icon={FileSpreadsheetIcon}
      title={name ?? "CSV file"}
      aside={
        <Flex align="center" gap="2" flexGrow="1" justify="end">
          <Button variant="soft" color="gray" size="1" onClick={() => setOpened(true)}>
            <Settings2Icon size={14} />
            Columns
          </Button>
          <IconButton
            variant="ghost"
            color="gray"
            size="1"
            aria-label="Leave the file out"
            onClick={onRemove}
          >
            <XIcon size={14} />
          </IconButton>
        </Flex>
      }
    >
      {error && !opened && (
        <Text size="2" color="red">
          {error.message}
        </Text>
      )}
      <Summary mapping={mapping} preview={preview} isReading={isReading} />

      <Dialog
        opened={opened}
        onClose={() => setOpened(false)}
        title={name ?? "CSV file"}
        footer={<Button onClick={() => setOpened(false)}>Done</Button>}
      >
        <Flex direction="column" gap="3">
          {error && (
            <Text size="2" color="red">
              {error.message}
            </Text>
          )}
          <SampleTable file={file} mapping={mapping} preview={preview} onAssign={onAssign} />
          <Summary mapping={mapping} preview={preview} isReading={isReading} withReasons />
        </Flex>
      </Dialog>
    </Section>
  );
}

// The file's first rows. Above each column, what it holds; unused columns are
// grey, and cells that keep their row out are marked.
function SampleTable({
  file,
  mapping,
  preview,
  onAssign,
}: {
  file: RecordFile;
  mapping: Mapping;
  preview: Preview | null;
  onAssign: (column: string, role: Role | null) => void;
}) {
  const roleOf = (column: string) => ROLES.find(({ value }) => mapping[value] === column)?.value;
  const badCells = new Set<string>();
  const badRows = new Set<number>();
  for (const issue of preview?.sampleIssues ?? []) {
    const roles = ISSUE_ROLES[issue.kind];
    if (roles.length === 0) badRows.add(issue.row);
    for (const role of roles) {
      const column = mapping[role];
      if (column) badCells.add(`${issue.row}:${column}`);
    }
  }
  const cell = { padding: "6px 10px", whiteSpace: "nowrap", textAlign: "left" } as const;

  return (
    <Box
      style={{
        overflowX: "auto",
        border: "1px solid var(--gray-6)",
        borderRadius: "var(--radius-3)",
      }}
    >
      <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
        <thead>
          <tr style={{ background: "var(--gray-2)" }}>
            {file.columns.map((column) => (
              <th
                key={column}
                style={{
                  ...cell,
                  verticalAlign: "bottom",
                  borderBottom: "1px solid var(--gray-6)",
                }}
              >
                <SmallChoice
                  label={`What ${column} holds`}
                  value={roleOf(column) ?? UNUSED}
                  options={CHOICES}
                  onChange={(value) => onAssign(column, value === UNUSED ? null : (value as Role))}
                />
                <div
                  style={{
                    marginTop: 6,
                    fontWeight: 500,
                    color: roleOf(column) ? "var(--gray-12)" : "var(--gray-9)",
                  }}
                >
                  {column}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {file.sample.map((row, index) => (
            <tr
              // The sample is the file's first rows in their order.
              key={`row-${index}-${row.join("|")}`}
              style={{
                borderBottom: "1px solid var(--gray-4)",
                background: badRows.has(index) ? "var(--amber-a3)" : undefined,
              }}
            >
              {file.columns.map((column, position) => (
                <td
                  key={column}
                  style={{
                    ...cell,
                    color: roleOf(column) ? "var(--gray-12)" : "var(--gray-9)",
                    background: badCells.has(`${index}:${column}`) ? "var(--amber-a4)" : undefined,
                  }}
                >
                  {row[position] ?? ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  );
}

// How many rows fit the log and what they give; or which columns are missing.
function Summary({
  mapping,
  preview,
  isReading,
  withReasons = false,
}: {
  mapping: Mapping;
  preview: Preview | null;
  isReading: boolean;
  withReasons?: boolean;
}) {
  if (isReading) {
    return (
      <Text size="2" color="gray">
        Reading the file…
      </Text>
    );
  }
  if (!preview) {
    const missing = [
      !mapping.flow && "the flow",
      !mapping.object && "the object",
      !mapping.quantity && "the quantity",
      !mapping.event && !(mapping.startTime && mapping.endTime) && "start and end, or the event",
    ].filter(Boolean);
    return (
      <Text size="2" color="amber">
        Missing: {missing.join(", ")}
      </Text>
    );
  }
  const flows = preview.flows.filter((flow) => flow.usableRows > 0).length;
  return (
    <Flex direction="column" gap="2">
      <Text size="2">
        {formatCount(preview.usableRows)} of {formatCount(preview.rows)} rows
        <Text color="gray">
          {` · ${formatCount(flows)} ${flows === 1 ? "flow" : "flows"}`}
          {preview.eventEnds > 0 && ` · ${formatCount(preview.eventEnds)} event ends`}
        </Text>
      </Text>
      {withReasons && preview.issues.length > 0 && (
        <Flex gap="2" wrap="wrap" align="center">
          {preview.issues.map((issue) => (
            <Badge key={issue.kind} color="amber" variant="soft">
              {formatCount(issue.rows)} × {ISSUES[issue.kind]}
            </Badge>
          ))}
        </Flex>
      )}
    </Flex>
  );
}
