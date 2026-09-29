import { CircleCheckIcon, CircleDashedIcon, CircleXIcon } from "lucide-react";
import type { ValidationResult } from "../../../data/overview/useValidateSocel";
import { Badge, Flex, Grid, Text, Tooltip } from "../../../ui";

const marks = {
  passed: { icon: CircleCheckIcon, color: "teal" },
  failed: { icon: CircleXIcon, color: "red" },
  skipped: { icon: CircleDashedIcon, color: "gray" },
} as const;

const severityColors = { error: "red", warning: "amber", info: "gray" } as const;

// The rules of a validation as one tile each - hover for the rule - and, below,
// what the rules that did not pass found.
export default function ValidationReport({ result }: { result: ValidationResult }) {
  const open = result.results.filter((check) => check.status !== "passed");

  return (
    <Flex direction="column" gap="4">
      <Grid columns={{ initial: "3", sm: String(result.results.length) }} gap="2">
        {result.results.map((check) => {
          const { icon: Icon, color } = marks[check.status];
          return (
            <Tooltip key={check.id} content={check.title}>
              <Flex
                direction="column"
                align="center"
                gap="1"
                py="3"
                aria-label={`${check.id}: ${check.status}`}
                style={{
                  borderRadius: "var(--radius-3)",
                  background: `var(--${color}-a3)`,
                  color: `var(--${color}-11)`,
                  cursor: "help",
                }}
              >
                <Icon size={18} aria-hidden />
                <Text size="2" weight="bold">
                  {check.id}
                </Text>
              </Flex>
            </Tooltip>
          );
        })}
      </Grid>

      {open.map((check) => (
        <Flex key={check.id} direction="column" gap="2">
          <Text size="2">
            <Text weight="bold" mr="2" style={{ color: `var(--${marks[check.status].color}-11)` }}>
              {check.id}
            </Text>
            {check.title}
          </Text>
          {check.reason && (
            <Text size="1" color="gray">
              {check.reason}
            </Text>
          )}
          {check.findings.map((finding) => (
            <Flex key={finding.message} gap="2" align="center">
              <Badge color={severityColors[finding.severity]} variant="soft">
                {finding.severity}
              </Badge>
              <Text size="1">{finding.message}</Text>
            </Flex>
          ))}
        </Flex>
      ))}
    </Flex>
  );
}
