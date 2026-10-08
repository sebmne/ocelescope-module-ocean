import { ChevronRightIcon, ExternalLinkIcon, GaugeIcon, TimerIcon, ZapIcon } from "lucide-react";
import { type ReactNode, useState } from "react";
import {
  AsyncBoundary,
  Badge,
  Box,
  Flex,
  Grid,
  IconButton,
  Section,
  Text,
  Tooltip,
  useColorOf,
} from "../../components";
import { formatCount } from "../../lib/format";
import { type Flow, useFlowInventory } from "./useFlowInventory";

// A grid, not a table: rows that unfold below themselves inside a Radix table's
// scroll area are not always repainted (WebKit) until something else changes.
// The count columns hold numbers in the millions.
const COLUMNS = "24px minmax(0, 1fr) 64px 88px 96px 96px 32px";

// The flows of the sOCEL; a row opens to the object types the flow is observed at.
// Single objects are never listed: a log has too many.
export default function FlowsSection() {
  const inventory = useFlowInventory();
  const [open, setOpen] = useState<ReadonlySet<string>>(new Set());

  const toggle = (flowId: string) =>
    setOpen((current) => {
      const next = new Set(current);
      next.has(flowId) ? next.delete(flowId) : next.add(flowId);
      return next;
    });

  return (
    <Section icon={GaugeIcon} title="Flows">
      <AsyncBoundary
        status={inventory}
        isEmpty={(flows) => flows.length === 0}
        loadingLabel="Reading the flows…"
        errorTitle="The flows could not be read"
        emptyState={{ title: "No flows", description: "This sOCEL declares no flows." }}
        onRetry={() => void inventory.refetch()}
      >
        {(flows) => (
          <Box
            role="table"
            aria-label="Flows"
            style={{
              border: "1px solid var(--gray-a5)",
              borderRadius: "var(--radius-4)",
              overflow: "hidden",
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
              <span />
              <HeaderCell>Flow</HeaderCell>
              <HeaderCell>Unit</HeaderCell>
              <HeaderCell end>Instances</HeaderCell>
              <HeaderCell end>
                <IconHeader icon={TimerIcon} label="Interval records" />
              </HeaderCell>
              <HeaderCell end>
                <IconHeader icon={ZapIcon} label="Event-linked records" />
              </HeaderCell>
              <span />
            </Grid>
            {flows.map((flow) => (
              <FlowRow
                key={flow.flowId}
                flow={flow}
                isOpen={open.has(flow.flowId)}
                onToggle={() => toggle(flow.flowId)}
              />
            ))}
          </Box>
        )}
      </AsyncBoundary>
    </Section>
  );
}

function FlowRow({
  flow,
  isOpen,
  onToggle,
}: {
  flow: Flow;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <Box style={{ borderTop: "1px solid var(--gray-a4)" }}>
      <Grid
        role="row"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-label={`${isOpen ? "Close" : "Open"} flow ${flow.flowId}`}
        columns={COLUMNS}
        align="center"
        gap="3"
        px="3"
        py="3"
        onClick={onToggle}
        onKeyDown={(event) => {
          if (
            event.target === event.currentTarget &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            onToggle();
          }
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          cursor: "pointer",
          background: hovered ? "var(--gray-a2)" : undefined,
          transition: "background 100ms",
        }}
      >
        <Flex
          style={{
            color: "var(--gray-10)",
            transform: isOpen ? "rotate(90deg)" : undefined,
            transition: "transform 150ms",
          }}
        >
          <ChevronRightIcon size={16} aria-hidden />
        </Flex>
        <Flex align="center" gap="2" minWidth="0">
          <Text size="2" weight="medium" wrap="nowrap">
            {flow.flowId}
          </Text>
          {flow.category && (
            <Badge color="gray" variant="soft" style={{ minWidth: 0 }}>
              <Text truncate>{flow.category}</Text>
            </Badge>
          )}
        </Flex>
        <Text size="2">{flow.unit}</Text>
        <Count value={flow.instances} />
        <Count value={flow.intervalRecords} />
        <Count value={flow.eventRecords} />
        <Flex justify="end" onClick={(event) => event.stopPropagation()}>
          {flow.externalRef && (
            <IconButton variant="ghost" color="gray" size="1" asChild>
              <a
                href={flow.externalRef}
                target="_blank"
                rel="noreferrer"
                aria-label="External reference"
              >
                <ExternalLinkIcon size={14} />
              </a>
            </IconButton>
          )}
        </Flex>
      </Grid>
      {isOpen && (
        <Box py="1" style={{ background: "var(--gray-a2)", borderTop: "1px solid var(--gray-a3)" }}>
          {flow.byObjectType.map((part) => (
            <Grid key={part.objectType} columns={COLUMNS} align="center" gap="3" px="3" py="1">
              <span />
              <Flex align="center" gap="2" minWidth="0">
                <TypeDot type={part.objectType} />
                <Text size="2" truncate>
                  {part.objectType}
                </Text>
                {part.contained > 0 && (
                  <Text size="1" color="gray" wrap="nowrap">
                    {formatCount(part.contained)} contained
                  </Text>
                )}
              </Flex>
              <span />
              <Count value={part.instances} />
              <Count value={part.intervalRecords} />
              <Count value={part.eventRecords} />
              <span />
            </Grid>
          ))}
        </Box>
      )}
    </Box>
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
    <Text size="2" align="right" style={{ fontVariantNumeric: "tabular-nums" }}>
      {formatCount(value)}
    </Text>
  );
}

// The colour an object type has everywhere in Ocelescope.
function TypeDot({ type }: { type: string }) {
  const colorOf = useColorOf("objectType");
  return (
    <span
      aria-hidden
      style={{
        flex: "none",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: colorOf(type),
      }}
    />
  );
}
