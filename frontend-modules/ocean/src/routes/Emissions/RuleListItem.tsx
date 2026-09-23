import { ActionIcon, Badge, Group, Paper, Text, UnstyledButton } from "@mantine/core";
import { Trash2Icon } from "lucide-react";
import { describeFactor, isRuleComplete, ruleTypeLabels } from "./ruleUtils";
import type { EmissionRule } from "./types";

interface RuleListItemProps {
  rule: EmissionRule;
  onEdit: () => void;
  onRemove: () => void;
}

// One line in the rules list. Clicking it opens the rule in the editor.
export default function RuleListItem({ rule, onEdit, onRemove }: RuleListItemProps) {
  return (
    <Paper withBorder radius="md">
      <Group wrap="nowrap" gap={0} pr="xs">
        <UnstyledButton onClick={onEdit} p="sm" style={{ flex: 1, minWidth: 0 }}>
          <Group justify="space-between" wrap="nowrap">
            <div style={{ minWidth: 0 }}>
              <Text fw={500} truncate c={rule.activity ? undefined : "dimmed"}>
                {rule.activity ?? "New rule"}
              </Text>
              <Text size="sm" c="dimmed" truncate>
                {describeFactor(rule)}
              </Text>
            </div>
            <Group gap="xs" wrap="nowrap" style={{ flexShrink: 0 }}>
              {!isRuleComplete(rule) && (
                <Badge color="orange" variant="light" tt="none">
                  Incomplete
                </Badge>
              )}
              <Badge color="gray" variant="light" tt="none">
                {ruleTypeLabels[rule.type]}
              </Badge>
            </Group>
          </Group>
        </UnstyledButton>

        {/* Next to the row's button, not inside it: nested buttons are invalid HTML. */}
        <ActionIcon variant="subtle" color="gray" onClick={onRemove} aria-label="Delete rule">
          <Trash2Icon size={16} aria-hidden />
        </ActionIcon>
      </Group>
    </Paper>
  );
}
