import { ChevronRightIcon, ExternalLinkIcon, GaugeIcon, TimerIcon, ZapIcon } from "lucide-react";
import { type ReactNode, useState } from "react";
import { type Flow, useFlowInventory } from "../../../data/overview/useFlowInventory";
import { useSocelStatus } from "../../../data/overview/useSocelStatus";
import { formatCount } from "../../../lib/format";
import { Badge, Box, Flex, Grid, IconButton, Section, Spinner, Text, Tooltip } from "../../../ui";
import ScopeTree from "./ScopeTree";

// A grid, not a table: rows that unfold below themselves inside a Radix table's
// scroll area are not always repainted (WebKit) until something else changes.
const COLUMNS = "24px minmax(0, 1fr) 64px 88px 48px 48px 32px";

// The flows of the sOCEL; a row opens its flow instances as nested metering scopes.
export default function FlowsSection() {
  const isSocel = useSocelStatus().data?.isSocel ?? false;
  const { data: flows } = useFlowInventory(isSocel);
  const [open, setOpen] = useState<ReadonlySet<string>>(new Set());

  if (!isSocel) return null;

  const toggle = (flowId: string) =>
    setOpen((current) => {
      const next = new Set(current);
      next.has(flowId) ? next.delete(flowId) : next.add(flowId);
      return next;
    });

  return (
    <Section icon={GaugeIcon} title="Flows">
      {!flows ? (
        <Flex justify="center" py="6">
          <Spinner size="3" />
        </Flex>
      ) : (
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
  const sum = (key: "intervalRecords" | "eventRecords") =>
    flow.instances.reduce((total, instance) => total + instance[key], 0);

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
          background: hovered ? "var(--accent-a2)" : undefined,
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
        <Count value={flow.instances.length} />
        <Count value={sum("intervalRecords")} />
        <Count value={sum("eventRecords")} />
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
        <Box
          px="5"
          py="2"
          style={{ background: "var(--gray-a2)", borderTop: "1px solid var(--gray-a3)" }}
        >
          <ScopeTree flow={flow} />
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
