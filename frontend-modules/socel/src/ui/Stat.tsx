import { Card, Flex, Text } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";

interface StatProps {
  label: string;
  /** The number, already formatted; "–" when there is none yet. */
  value: string;
  unit?: string;
  /** A short line below the number, e.g. its share of a total. */
  hint?: string;
  icon: LucideIcon;
  /** The page's key figure: set in the accent colour. */
  highlight?: boolean;
}

// One key figure: label, big number with unit, and a hint.
export default function Stat({ label, value, unit, hint, icon: Icon, highlight }: StatProps) {
  return (
    <Card
      size="2"
      style={
        highlight
          ? {
              background: "linear-gradient(135deg, var(--accent-3), var(--accent-2))",
              boxShadow: "inset 0 0 0 1px var(--accent-a5)",
            }
          : undefined
      }
    >
      <Flex direction="column" gap="2">
        <Flex
          align="center"
          gap="2"
          style={{ color: highlight ? "var(--accent-11)" : "var(--gray-11)" }}
        >
          <Icon size={15} aria-hidden />
          <Text size="2" weight="medium">
            {label}
          </Text>
        </Flex>
        <Flex align="baseline" gap="1" wrap="wrap">
          <Text
            size="7"
            weight="bold"
            style={{
              fontVariantNumeric: "tabular-nums",
              letterSpacing: "-0.02em",
              color: highlight ? "var(--accent-12)" : undefined,
            }}
          >
            {value}
          </Text>
          {unit && (
            <Text
              size="2"
              color={highlight ? undefined : "gray"}
              style={highlight ? { color: "var(--accent-11)" } : undefined}
            >
              {unit}
            </Text>
          )}
        </Flex>
        <Text size="1" color="gray" style={{ minHeight: "1lh" }}>
          {hint}
        </Text>
      </Flex>
    </Card>
  );
}
