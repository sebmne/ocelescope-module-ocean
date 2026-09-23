import { Divider, Group, Stack, Text } from "@mantine/core";
import { CloudIcon } from "lucide-react";
import Section from "./Section";

function formatKg(value: number | undefined) {
  return value === undefined
    ? "–"
    : `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} kg`;
}

// TODO(backend): take the imported and rule-based totals as props.
export default function EmissionsOverview() {
  const imported: number | undefined = undefined;
  const ruleBased: number | undefined = undefined;
  const total: number | undefined = undefined;

  return (
    <Section icon={CloudIcon} title="Total emissions">
      <Stack gap="md">
        <div>
          <Text fz={32} fw={700} lh={1.1}>
            {formatKg(total)}
          </Text>
          <Text size="sm" c="dimmed">
            CO₂e
          </Text>
        </div>
        <Divider />
        <Stack gap={4}>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Rule-based</Text>
            <Text size="sm">{formatKg(ruleBased)}</Text>
          </Group>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Imported</Text>
            <Text size="sm">{formatKg(imported)}</Text>
          </Group>
        </Stack>
      </Stack>
    </Section>
  );
}
