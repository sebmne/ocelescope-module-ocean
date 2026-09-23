import { Center, Stack, Text } from "@mantine/core";
import { ChartColumnIcon } from "lucide-react";
import Section from "./Section";

// TODO(backend): take the allocated object emissions and render a histogram
// of CO₂e per object (e.g. BarChart from @ocelescope/core).
export default function ObjectEmissionsSection() {
  return (
    <Section icon={ChartColumnIcon} title="Object emissions">
      <Center mih={160}>
        <Stack gap={4} align="center">
          <ChartColumnIcon size={28} color="var(--mantine-color-dimmed)" aria-hidden />
          <Text size="sm" c="dimmed" ta="center" maw={260}>
            Allocate emissions to objects to see how they are distributed.
          </Text>
        </Stack>
      </Center>
    </Section>
  );
}
