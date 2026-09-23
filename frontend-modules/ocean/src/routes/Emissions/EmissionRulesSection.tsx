import { Button, Drawer, Group, Stack, Text, Tooltip } from "@mantine/core";
import { ListChecksIcon, PlusIcon } from "lucide-react";
import { useState } from "react";
import RuleEditor from "./RuleEditor";
import RuleListItem from "./RuleListItem";
import { isRuleComplete } from "./ruleUtils";
import Section from "./Section";
import type { EmissionRule } from "./types";

interface EmissionRulesSectionProps {
  rules: readonly EmissionRule[];
  onAdd: () => number;
  onChange: (id: number, changes: Partial<EmissionRule>) => void;
  onRemove: (id: number) => void;
}

export default function EmissionRulesSection({ rules, onAdd, onChange, onRemove }: EmissionRulesSectionProps) {
  // The rule open in the drawer. Only this section cares, so the state lives here.
  const [editingId, setEditingId] = useState<number | null>(null);
  const editingRule = rules.find((rule) => rule.id === editingId);

  const completeCount = rules.filter(isRuleComplete).length;

  return (
    <Section
      icon={ListChecksIcon}
      title="Emission rules"
      description="Assign emissions to the events of an activity."
      actions={
        <Button variant="light" size="xs" leftSection={<PlusIcon size={14} />} onClick={() => setEditingId(onAdd())}>
          Add rule
        </Button>
      }
    >
      {rules.length === 0 ? (
        <Text size="sm" c="dimmed" ta="center" py="lg">
          No rules yet.
        </Text>
      ) : (
        <Stack gap="xs">
          {rules.map((rule) => (
            <RuleListItem
              key={rule.id}
              rule={rule}
              onEdit={() => setEditingId(rule.id)}
              onRemove={() => onRemove(rule.id)}
            />
          ))}
        </Stack>
      )}

      <Group justify="space-between">
        <Text size="sm" c="dimmed">
          {rules.length > 0 && `${completeCount} of ${rules.length} rules complete`}
        </Text>
        {/* TODO(backend): send the complete rules and show the result in the overview. */}
        <Tooltip label="Needs the OCEAn backend">
          <Button disabled>Compute emissions</Button>
        </Tooltip>
      </Group>

      <Drawer
        // Portal into the r4pm Theme that wraps the app, not <body>: the r4pm
        // inputs in the editor lose their styles outside it.
        portalProps={{ target: ".radix-themes" }}
        opened={editingRule !== undefined}
        onClose={() => setEditingId(null)}
        position="right"
        size="md"
        title={<Text fw={600}>Edit rule</Text>}
      >
        {editingRule && (
          <RuleEditor rule={editingRule} onChange={(changes) => onChange(editingRule.id, changes)} />
        )}
      </Drawer>
    </Section>
  );
}
