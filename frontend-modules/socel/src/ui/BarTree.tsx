import { Box, Flex, Text, Tooltip } from "@r4pm/components/ui";
import { ChevronRightIcon } from "lucide-react";
import { useState } from "react";

export interface BarNode {
  id: string;
  label: string;
  value: number;
  /** A tooltip on the value, e.g. how much of it is the node's own. */
  valueHint?: string;
  /** accent: a node that matters most; muted: one that stands aside, e.g. "unclassified". */
  tone?: "accent" | "neutral" | "muted";
  children: readonly BarNode[];
}

interface BarTreeProps {
  nodes: readonly BarNode[];
  format: (value: number) => string;
  /** Levels open at first: 1 shows the roots' children. */
  openDepth?: number;
}

const fills = { accent: "var(--accent-a5)", neutral: "var(--gray-a4)", muted: "var(--gray-a2)" };

// A tree of labelled values, each drawn as a bar relative to the largest root;
// nodes with children fold.
export default function BarTree({ nodes, format, openDepth = 1 }: BarTreeProps) {
  const max = Math.max(1, ...nodes.map((node) => node.value));
  return (
    <Flex direction="column" gap="1" role="tree">
      {nodes.map((node) => (
        <BarTreeRow
          key={node.id}
          node={node}
          depth={0}
          max={max}
          format={format}
          openDepth={openDepth}
        />
      ))}
    </Flex>
  );
}

interface RowProps {
  node: BarNode;
  depth: number;
  max: number;
  format: (value: number) => string;
  openDepth: number;
}

function BarTreeRow({ node, depth, max, format, openDepth }: RowProps) {
  const [open, setOpen] = useState(depth < openDepth);
  const hasChildren = node.children.length > 0;
  const value = (
    <Text size="2" weight="medium" style={{ fontVariantNumeric: "tabular-nums" }}>
      {format(node.value)}
    </Text>
  );

  return (
    <>
      <Flex
        role="treeitem"
        aria-expanded={hasChildren ? open : undefined}
        align="center"
        gap="1"
        style={{ paddingLeft: depth * 16 }}
      >
        <Box
          flexShrink="0"
          onClick={() => hasChildren && setOpen(!open)}
          style={{
            width: 16,
            color: "var(--gray-10)",
            cursor: hasChildren ? "pointer" : undefined,
            visibility: hasChildren ? undefined : "hidden",
            transform: open ? "rotate(90deg)" : undefined,
            transition: "transform 150ms",
            display: "flex",
          }}
        >
          <ChevronRightIcon size={14} aria-label={open ? "Fold" : "Unfold"} />
        </Box>
        <Box
          position="relative"
          flexGrow="1"
          minWidth="0"
          onClick={() => hasChildren && setOpen(!open)}
          style={{ cursor: hasChildren ? "pointer" : undefined }}
        >
          <Box
            position="absolute"
            inset="0"
            style={{
              width: `${(node.value / max) * 100}%`,
              background: fills[node.tone ?? "neutral"],
              borderRadius: "var(--radius-2)",
            }}
          />
          <Flex position="relative" justify="between" gap="3" px="2" py="1">
            <Text size="2" truncate color={node.tone === "muted" ? "gray" : undefined}>
              {node.label}
            </Text>
            {node.valueHint ? <Tooltip content={node.valueHint}>{value}</Tooltip> : value}
          </Flex>
        </Box>
      </Flex>
      {open &&
        node.children.map((child) => (
          <BarTreeRow
            key={child.id}
            node={child}
            depth={depth + 1}
            max={max}
            format={format}
            openDepth={openDepth}
          />
        ))}
    </>
  );
}
