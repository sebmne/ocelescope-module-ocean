import { Box, Flex, Text, Tooltip } from "@r4pm/components/ui";

export interface Proportion {
  label: string;
  value: number;
  /** A Radix colour scale, e.g. "teal"; "accent" for the theme's. */
  color: string;
  /** A sentence on what this part is. */
  description?: string;
}

interface ProportionBarProps {
  parts: readonly Proportion[];
  /** How a part's value is shown in the legend. */
  format: (value: number) => string;
}

const fill = (color: string) => `var(--${color}-9)`;

// How a whole divides into parts: one bar in segments, with a legend below.
export default function ProportionBar({ parts, format }: ProportionBarProps) {
  const total = parts.reduce((sum, part) => sum + part.value, 0);

  return (
    <Flex direction="column" gap="3">
      <Flex
        style={{
          height: 10,
          borderRadius: 999,
          overflow: "hidden",
          background: "var(--gray-a3)",
          gap: 2,
        }}
        role="img"
        aria-label={parts.map((part) => `${part.label}: ${format(part.value)}`).join(", ")}
      >
        {total > 0 &&
          parts
            .filter((part) => part.value > 0)
            .map((part) => (
              <Box
                key={part.label}
                style={{ flexGrow: part.value, background: fill(part.color) }}
              />
            ))}
      </Flex>

      <Flex direction="column" gap="2">
        {parts.map((part) => (
          <Flex key={part.label} align="center" justify="between" gap="3">
            <Flex align="center" gap="2" minWidth="0">
              <Box
                flexShrink="0"
                style={{ width: 8, height: 8, borderRadius: 2, background: fill(part.color) }}
              />
              {part.description ? (
                <Tooltip content={part.description}>
                  <Text size="2" color="gray" truncate style={{ cursor: "help" }}>
                    {part.label}
                  </Text>
                </Tooltip>
              ) : (
                <Text size="2" color="gray" truncate>
                  {part.label}
                </Text>
              )}
            </Flex>
            <Flex gap="3" flexShrink="0" style={{ fontVariantNumeric: "tabular-nums" }}>
              <Text size="2" color="gray">
                {total > 0 &&
                  (part.value / total).toLocaleString(undefined, {
                    style: "percent",
                    maximumFractionDigits: 0,
                  })}
              </Text>
              <Text size="2" weight="medium" style={{ minWidth: 72, textAlign: "right" }}>
                {format(part.value)}
              </Text>
            </Flex>
          </Flex>
        ))}
      </Flex>
    </Flex>
  );
}
