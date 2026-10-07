import { CornerDownRightIcon, TimerIcon, ZapIcon } from "lucide-react";
import { Badge, Box, Flex, Text, Tooltip } from "../../components";
import { formatCount } from "../../lib/format";
import { type ScopeNode, scopeTree } from "./meteringScopes";
import type { Flow } from "./useFlowInventory";

type Instance = Flow["instances"][number];

// A flow's instances as nested metering scopes, each with its records.
export default function ScopeTree({ flow }: { flow: Flow }) {
  return (
    <Flex direction="column" gap="1">
      {scopeTree(flow.instances).map((node) => (
        <ScopeRow key={node.instance.objectId} node={node} depth={0} />
      ))}
    </Flex>
  );
}

function ScopeRow({ node, depth }: { node: ScopeNode<Instance>; depth: number }) {
  const { objectId, objectType, intervalRecords, eventRecords } = node.instance;
  return (
    <>
      <Flex align="center" justify="between" gap="3" py="1" style={{ paddingLeft: depth * 20 }}>
        <Flex align="center" gap="2" minWidth="0">
          {depth > 0 && (
            <Box style={{ color: "var(--gray-8)" }} flexShrink="0">
              <CornerDownRightIcon size={14} aria-hidden />
            </Box>
          )}
          <Text size="2" weight="medium" truncate>
            {objectId}
          </Text>
          <Badge color="gray" variant="soft" size="1">
            {objectType}
          </Badge>
        </Flex>
        <Flex gap="3" flexShrink="0">
          <RecordCount icon={TimerIcon} count={intervalRecords} label="Interval records" />
          <RecordCount icon={ZapIcon} count={eventRecords} label="Event-linked records" />
        </Flex>
      </Flex>
      {node.children.map((child) => (
        <ScopeRow key={child.instance.objectId} node={child} depth={depth + 1} />
      ))}
    </>
  );
}

function RecordCount({
  icon: Icon,
  count,
  label,
}: {
  icon: typeof TimerIcon;
  count: number;
  label: string;
}) {
  return (
    <Tooltip content={label}>
      <Flex
        align="center"
        gap="1"
        style={{
          minWidth: 44,
          justifyContent: "flex-end",
          color: count > 0 ? "var(--gray-12)" : "var(--gray-8)",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        <Icon size={13} aria-label={label} />
        <Text size="2">{formatCount(count)}</Text>
      </Flex>
    </Tooltip>
  );
}
