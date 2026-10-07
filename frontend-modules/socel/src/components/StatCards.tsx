import { Card, Flex, Heading, Text } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";

export interface StatItem {
  label: string;
  /** The number, already formatted; "–" when there is none. */
  value: string;
  /** A short line below the label, e.g. the number's share of a total. */
  hint?: string;
  icon: LucideIcon;
}

// Key figures side by side: the layout of r4pm's StatCards (number, label, hint),
// with an icon to tell the figures apart at a glance.
export default function StatCards({ items }: { items: readonly StatItem[] }) {
  return (
    <Flex gap="3" wrap="wrap" align="stretch">
      {items.map(({ label, value, hint, icon: Icon }) => (
        <Card key={label} style={{ minWidth: 150, flex: 1 }}>
          <Flex direction="column" gap="2" p="1" height="100%">
            <Flex justify="between" align="start" gap="2">
              <Heading size="6" style={{ fontVariantNumeric: "tabular-nums" }}>
                {value}
              </Heading>
              <Flex flexShrink="0" style={{ color: "var(--gray-9)" }}>
                <Icon size={16} aria-hidden />
              </Flex>
            </Flex>
            <Text size="2" weight="medium">
              {label}
            </Text>
            {hint && (
              <Text size="1" color="gray">
                {hint}
              </Text>
            )}
          </Flex>
        </Card>
      ))}
    </Flex>
  );
}
