import { ChevronLeftIcon, ChevronRightIcon, TimerIcon, ZapIcon } from "lucide-react";
import { type ReactNode, useState } from "react";
import { AsyncBoundary, Box, Flex, Grid, IconButton, Text, Tooltip } from "../../components";
import { formatCount, formatTimestamp } from "../../lib/format";
import { type FlowRecord, RECORD_PAGE_SIZE, useFlowRecords } from "./useFlowRecords";

const COLUMNS = "24px 170px 170px minmax(0, 1fr) minmax(0, 1fr) 120px";

const formatQuantity = (quantity: number) =>
  quantity.toLocaleString(undefined, { maximumFractionDigits: 3 });

// A flow's records at one object, a page at a time: when each was taken, and
// for an event-linked record, its event.
export default function RecordList({
  flowId,
  objectId,
  unit,
}: {
  flowId: string;
  objectId: string;
  unit: string;
}) {
  const [page, setPage] = useState(0);
  const records = useFlowRecords(flowId, objectId, page);
  const total = records.data?.total ?? 0;

  return (
    <Box
      px="3"
      py="2"
      style={{ background: "var(--gray-a2)", borderTop: "1px solid var(--gray-a3)" }}
    >
      <AsyncBoundary
        status={records}
        isEmpty={(data) => data.items.length === 0}
        loadingLabel="Reading the records…"
        errorTitle="The records could not be read"
        emptyState={{ title: "No records", description: "This object has no records itself." }}
        onRetry={() => void records.refetch()}
      >
        {(data) => (
          <Flex direction="column" gap="2">
            <Box
              role="table"
              aria-label={`Records of ${flowId} at ${objectId}`}
              style={{
                opacity: records.isPlaceholderData ? 0.6 : 1,
                transition: "opacity 100ms",
              }}
            >
              <Grid role="row" columns={COLUMNS} align="center" gap="3" py="1">
                <span />
                <HeaderCell>Start</HeaderCell>
                <HeaderCell>End</HeaderCell>
                <HeaderCell>Event</HeaderCell>
                <HeaderCell>Activity</HeaderCell>
                <HeaderCell end>Quantity</HeaderCell>
              </Grid>
              {data.items.map((record) => (
                <RecordRow key={record.recordId} record={record} unit={unit} />
              ))}
            </Box>
            {total > RECORD_PAGE_SIZE && (
              <Flex align="center" justify="between" gap="3">
                <Text size="1" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatCount(page * RECORD_PAGE_SIZE + 1)}–
                  {formatCount(Math.min(total, (page + 1) * RECORD_PAGE_SIZE))} of{" "}
                  {formatCount(total)} records
                </Text>
                <Flex gap="2">
                  <IconButton
                    size="1"
                    variant="soft"
                    color="gray"
                    aria-label="Previous records"
                    disabled={page === 0}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeftIcon size={14} />
                  </IconButton>
                  <IconButton
                    size="1"
                    variant="soft"
                    color="gray"
                    aria-label="Next records"
                    disabled={(page + 1) * RECORD_PAGE_SIZE >= total}
                    onClick={() => setPage(page + 1)}
                  >
                    <ChevronRightIcon size={14} />
                  </IconButton>
                </Flex>
              </Flex>
            )}
          </Flex>
        )}
      </AsyncBoundary>
    </Box>
  );
}

function RecordRow({ record, unit }: { record: FlowRecord; unit: string }) {
  const isEvent = record.kind === "event";
  const Icon = isEvent ? ZapIcon : TimerIcon;
  const label = isEvent ? "Event-linked record" : "Interval record";
  return (
    <Grid
      role="row"
      columns={COLUMNS}
      align="center"
      gap="3"
      py="1"
      style={{ borderTop: "1px solid var(--gray-a3)" }}
    >
      <Flex style={{ color: "var(--gray-10)" }}>
        <Tooltip content={label}>
          <Icon size={14} aria-label={label} />
        </Tooltip>
      </Flex>
      <Cell>{formatTimestamp(record.start)}</Cell>
      <Cell>{record.end ? formatTimestamp(record.end) : null}</Cell>
      <Cell>{record.eventId}</Cell>
      <Cell>{record.activity}</Cell>
      <Text size="2" align="right" wrap="nowrap" style={{ fontVariantNumeric: "tabular-nums" }}>
        {formatQuantity(record.quantity)} {unit}
      </Text>
    </Grid>
  );
}

// A value, or a dash where the record has none.
function Cell({ children }: { children: ReactNode }) {
  return children ? (
    <Text size="2" truncate style={{ fontVariantNumeric: "tabular-nums" }}>
      {children}
    </Text>
  ) : (
    <Text size="2" color="gray">
      –
    </Text>
  );
}

function HeaderCell({ children, end }: { children: ReactNode; end?: boolean }) {
  return (
    <Flex role="columnheader" justify={end ? "end" : "start"}>
      <Text size="1" color="gray" weight="medium">
        {children}
      </Text>
    </Flex>
  );
}
