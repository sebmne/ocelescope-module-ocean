import { Box, Flex, Text, Tooltip } from "@r4pm/components/ui";
import type { ReactNode } from "react";

interface SplitBarProps {
  label: ReactNode;
  /** The part that went somewhere, drawn in the accent colour. */
  done: number;
  /** The rest, drawn in amber. */
  rest: number;
  /** The largest total among the bars shown together, for their lengths. */
  max: number;
  format: (value: number) => string;
  doneLabel: string;
  restLabel: string;
}

// One total as a bar in two parts, e.g. attributed and remainder, sized
// relative to the largest total of its list.
export default function SplitBar({
  label,
  done,
  rest,
  max,
  format,
  doneLabel,
  restLabel,
}: SplitBarProps) {
  const scale = (value: number) => `${(Math.abs(value) / Math.max(max, 1e-12)) * 100}%`;
  return (
    <Flex direction="column" gap="1">
      <Flex justify="between" gap="3">
        <Text size="2" truncate>
          {label}
        </Text>
        <Text size="2" weight="medium" style={{ fontVariantNumeric: "tabular-nums" }}>
          {format(done + rest)}
        </Text>
      </Flex>
      <Flex style={{ height: 8, borderRadius: 999, background: "var(--gray-a3)", gap: 2 }}>
        {done !== 0 && (
          <Tooltip content={`${doneLabel}: ${format(done)}`}>
            <Box style={{ width: scale(done), background: "var(--accent-9)", borderRadius: 999 }} />
          </Tooltip>
        )}
        {rest !== 0 && (
          <Tooltip content={`${restLabel}: ${format(rest)}`}>
            <Box style={{ width: scale(rest), background: "var(--amber-9)", borderRadius: 999 }} />
          </Tooltip>
        )}
      </Flex>
    </Flex>
  );
}
