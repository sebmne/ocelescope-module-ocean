import { Grid, Stack, Text, Title } from "@mantine/core";
import EmissionRulesSection from "./EmissionRulesSection";
import EmissionsOverview from "./EmissionsOverview";
import ObjectAllocationSection from "./ObjectAllocationSection";
import ObjectEmissionsSection from "./ObjectEmissionsSection";
import { useEmissionRules } from "./useEmissionRules";

// The OCEAn workflow on one page: set up on the left, results on the right.
export default function Emissions() {
  const [rules, addRule, updateRule, removeRule] = useEmissionRules();

  return (
    <Stack gap="xl" p="xl" maw={1400}>
      <div>
        <Title order={2}>Emission analysis</Title>
        <Text c="dimmed">
          Define how events emit CO₂e, then allocate the emissions to objects.
        </Text>
      </div>

      <Grid gap="xl" align="flex-start">
        <Grid.Col span={{ base: 12, lg: 7 }}>
          <Stack gap="xl">
            <EmissionRulesSection
              rules={rules}
              onAdd={addRule}
              onChange={updateRule}
              onRemove={removeRule}
            />
            <ObjectAllocationSection />
          </Stack>
        </Grid.Col>

        {/* Results stay in view while scrolling through the setup. */}
        <Grid.Col span={{ base: 12, lg: 5 }} style={{ position: "sticky", top: "var(--mantine-spacing-xl)" }}>
          <Stack gap="xl">
            <EmissionsOverview />
            <ObjectEmissionsSection />
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
