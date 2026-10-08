import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ListIcon,
  SearchIcon,
  TimerIcon,
  XIcon,
  ZapIcon,
} from "lucide-react";
import { type ReactNode, useState } from "react";
import {
  AsyncBoundary,
  Badge,
  Box,
  Flex,
  Grid,
  IconButton,
  Section,
  Select,
  Text,
  TextField,
  Tooltip,
  useColorOf,
} from "../../components";
import { useFlowInventory } from "../../hooks/useFlowInventory";
import { formatCount } from "../../lib/format";
import {
  type FlowInstance,
  type InstanceOrder,
  PAGE_SIZE,
  useFlowInstances,
} from "./useFlowInstances";

// Radix has no empty value: this one stands for "every type".
const ALL = "__all__";
const COLUMNS = "minmax(0, 1.6fr) minmax(0, 1fr) 96px 96px 96px 140px";

const formatQuantity = (quantity: number) =>
  quantity.toLocaleString(undefined, { maximumFractionDigits: 1 });

// The objects a flow is observed at, a page at a time: a log has too many to
// list. What lies inside what is explored by stepping in, one level at a time.
export default function FlowInstances({
  flowId,
  initialObjectType,
}: {
  flowId: string;
  /** The object type the list starts with; null for all. */
  initialObjectType: string | null;
}) {
  const flow = useFlowInventory().data?.find((candidate) => candidate.flowId === flowId);
  const [objectType, setObjectType] = useState(initialObjectType);
  const [inside, setInside] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [order, setOrder] = useState<InstanceOrder>("quantity");
  const [page, setPage] = useState(0);

  // A changed filter starts at its first page.
  const filterKey = [objectType, inside, search, order].join("\u0000");
  const [seenKey, setSeenKey] = useState(filterKey);
  if (seenKey !== filterKey) {
    setSeenKey(filterKey);
    setPage(0);
  }

  const instances = useFlowInstances(flowId, {
    objectType,
    inside,
    search,
    order,
    page,
  });
  const total = instances.data?.total ?? 0;
  // What lies inside an object is shown whatever its type.
  const stepInto = (objectId: string) => {
    setInside(objectId);
    setObjectType(null);
  };

  return (
    <Section
      icon={ListIcon}
      title="Objects"
      aside={
        instances.data && (
          <Badge color="gray" variant="soft">
            {formatCount(total)}
          </Badge>
        )
      }
    >
      <Flex direction="column" gap="3">
        <Flex gap="3" wrap="wrap">
          <Box flexGrow="1" style={{ minWidth: 220 }}>
            <TextField.Root
              aria-label="Search object id"
              placeholder="Search object id"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            >
              <TextField.Slot>
                <SearchIcon size={14} />
              </TextField.Slot>
            </TextField.Root>
          </Box>
          <Select.Root
            value={objectType ?? ALL}
            onValueChange={(type) => setObjectType(type === ALL ? null : type)}
          >
            <Select.Trigger aria-label="Object type" style={{ width: 220 }} />
            <Select.Content position="popper">
              <Select.Item value={ALL}>All object types</Select.Item>
              {(flow?.byObjectType ?? []).map((part) => (
                <Select.Item key={part.objectType} value={part.objectType}>
                  {part.objectType} · {formatCount(part.instances)}
                </Select.Item>
              ))}
            </Select.Content>
          </Select.Root>
          <Select.Root value={order} onValueChange={(value) => setOrder(value as InstanceOrder)}>
            <Select.Trigger aria-label="Order" style={{ width: 180 }} />
            <Select.Content position="popper">
              <Select.Item value="quantity">Largest quantity first</Select.Item>
              <Select.Item value="object">By object id</Select.Item>
            </Select.Content>
          </Select.Root>
        </Flex>

        {inside && (
          <Flex align="center" gap="2" wrap="wrap">
            <Text size="2" color="gray">
              Inside
            </Text>
            {(instances.data?.path ?? [inside]).map((objectId, index, path) => (
              <Flex key={objectId} align="center" gap="2">
                {index > 0 && (
                  <Flex style={{ color: "var(--gray-8)" }}>
                    <ChevronRightIcon size={14} aria-hidden />
                  </Flex>
                )}
                {index === path.length - 1 ? (
                  <Badge variant="soft" size="2">
                    {objectId}
                    <IconButton
                      size="1"
                      variant="ghost"
                      aria-label="Show all objects"
                      onClick={() => setInside(null)}
                    >
                      <XIcon size={12} />
                    </IconButton>
                  </Badge>
                ) : (
                  <Badge asChild color="gray" variant="soft" size="2">
                    <button
                      type="button"
                      onClick={() => stepInto(objectId)}
                      style={{ cursor: "pointer" }}
                    >
                      {objectId}
                    </button>
                  </Badge>
                )}
              </Flex>
            ))}
          </Flex>
        )}

        <AsyncBoundary
          status={instances}
          isEmpty={(data) => data.rows.length === 0}
          loadingLabel="Reading the objects…"
          errorTitle="The objects could not be read"
          emptyState={{ title: "No objects", description: "Nothing matches these filters." }}
          onRetry={() => void instances.refetch()}
        >
          {(data) => (
            <Box
              role="table"
              aria-label={`Objects of ${flowId}`}
              style={{
                border: "1px solid var(--gray-a5)",
                borderRadius: "var(--radius-4)",
                overflow: "hidden",
                opacity: instances.isPlaceholderData ? 0.6 : 1,
                transition: "opacity 100ms",
              }}
            >
              <Grid
                role="row"
                columns={COLUMNS}
                align="center"
                gap="3"
                px="3"
                py="2"
                style={{ background: "var(--gray-a2)" }}
              >
                <HeaderCell>Object</HeaderCell>
                <HeaderCell>Inside</HeaderCell>
                <HeaderCell end>Contains</HeaderCell>
                <HeaderCell end>
                  <IconHeader icon={TimerIcon} label="Interval records" />
                </HeaderCell>
                <HeaderCell end>
                  <IconHeader icon={ZapIcon} label="Event-linked records" />
                </HeaderCell>
                <HeaderCell end>Quantity</HeaderCell>
              </Grid>
              {data.rows.map((row) => (
                <InstanceRow
                  key={row.objectId}
                  row={row}
                  unit={flow?.unit ?? ""}
                  onStepInto={stepInto}
                />
              ))}
            </Box>
          )}
        </AsyncBoundary>

        {total > PAGE_SIZE && (
          <Flex align="center" justify="between" gap="3">
            <Text size="2" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
              {formatCount(page * PAGE_SIZE + 1)}–
              {formatCount(Math.min(total, (page + 1) * PAGE_SIZE))} of {formatCount(total)}
            </Text>
            <Flex gap="2">
              <IconButton
                variant="soft"
                color="gray"
                aria-label="Previous page"
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeftIcon size={16} />
              </IconButton>
              <IconButton
                variant="soft"
                color="gray"
                aria-label="Next page"
                disabled={(page + 1) * PAGE_SIZE >= total}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRightIcon size={16} />
              </IconButton>
            </Flex>
          </Flex>
        )}
      </Flex>
    </Section>
  );
}

function InstanceRow({
  row,
  unit,
  onStepInto,
}: {
  row: FlowInstance;
  unit: string;
  onStepInto: (objectId: string) => void;
}) {
  const colorOf = useColorOf("objectType");
  return (
    <Grid
      role="row"
      columns={COLUMNS}
      align="center"
      gap="3"
      px="3"
      py="2"
      style={{ borderTop: "1px solid var(--gray-a4)" }}
    >
      <Flex align="center" gap="2" minWidth="0">
        <span
          aria-hidden
          style={{
            flex: "none",
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: colorOf(row.objectType),
          }}
        />
        <Text size="2" weight="medium" truncate>
          {row.objectId}
        </Text>
        <Badge color="gray" variant="soft" size="1">
          {row.objectType}
        </Badge>
      </Flex>
      <Flex minWidth="0">
        {row.parentObjectId ? (
          <StepIn
            label={`Show what lies inside ${row.parentObjectId}`}
            onClick={() => onStepInto(row.parentObjectId as string)}
          >
            {row.parentObjectId}
          </StepIn>
        ) : (
          <Text size="2" color="gray">
            –
          </Text>
        )}
      </Flex>
      <Flex justify="end">
        {row.contains > 0 ? (
          <StepIn
            label={`Show the ${row.contains} objects inside ${row.objectId}`}
            onClick={() => onStepInto(row.objectId)}
          >
            {formatCount(row.contains)}
          </StepIn>
        ) : (
          <Text size="2" color="gray">
            –
          </Text>
        )}
      </Flex>
      <Count value={row.intervalRecords} />
      <Count value={row.eventRecords} />
      <Text size="2" align="right" style={{ fontVariantNumeric: "tabular-nums" }}>
        {formatQuantity(row.quantity)} {unit}
      </Text>
    </Grid>
  );
}

// A link that steps into an object: shows what lies inside it.
function StepIn({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <Tooltip content={label}>
      <Text asChild size="2" color="blue" truncate>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          style={{
            all: "unset",
            cursor: "pointer",
            color: "var(--accent-11)",
            fontSize: "var(--font-size-2)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {children}
        </button>
      </Text>
    </Tooltip>
  );
}

function HeaderCell({ children, end }: { children: ReactNode; end?: boolean }) {
  return (
    <Flex role="columnheader" justify={end ? "end" : "start"}>
      <Text size="2" weight="bold">
        {children}
      </Text>
    </Flex>
  );
}

function IconHeader({ icon: Icon, label }: { icon: typeof TimerIcon; label: string }) {
  return (
    <Tooltip content={label}>
      <Icon size={14} aria-label={label} />
    </Tooltip>
  );
}

function Count({ value }: { value: number }) {
  return (
    <Text
      size="2"
      align="right"
      color={value === 0 ? "gray" : undefined}
      style={{ fontVariantNumeric: "tabular-nums" }}
    >
      {formatCount(value)}
    </Text>
  );
}
