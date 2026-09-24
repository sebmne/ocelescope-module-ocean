import { Trash2Icon } from "lucide-react";
import {
  describeFactor,
  describeUnit,
  type EmissionRuleDraft,
  isRuleComplete,
} from "../../../model/emissionRules";
import { Badge, ClickableRow, IconButton, Table, Text, Tooltip, VisuallyHidden } from "../../../ui";

interface RuleTableProps {
  rules: readonly EmissionRuleDraft[];
  onEdit: (id: string) => void;
  onRemove: (id: string) => void;
}

// The rules at a glance: which activity emits how much, per what. A row opens the rule.
export default function RuleTable({ rules, onEdit, onRemove }: RuleTableProps) {
  return (
    <Table.Root variant="surface" size="2">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeaderCell>Activity</Table.ColumnHeaderCell>
          <Table.ColumnHeaderCell>Emission factor</Table.ColumnHeaderCell>
          <Table.ColumnHeaderCell width="1%">
            <VisuallyHidden>Actions</VisuallyHidden>
          </Table.ColumnHeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {rules.map((rule) => (
          <ClickableRow
            key={rule.id}
            label={`Edit rule ${rule.activity ?? "without activity"}`}
            onClick={() => onEdit(rule.id)}
            actions={
              <>
                {!isRuleComplete(rule) && (
                  <Tooltip content="Incomplete rules are left out when computing.">
                    <Badge color="amber" variant="soft">
                      Incomplete
                    </Badge>
                  </Tooltip>
                )}
                <IconButton
                  variant="ghost"
                  color="gray"
                  size="1"
                  onClick={() => onRemove(rule.id)}
                  aria-label="Delete rule"
                >
                  <Trash2Icon size={15} aria-hidden />
                </IconButton>
              </>
            }
          >
            <Table.RowHeaderCell>
              <Text weight="medium" color={rule.activity ? undefined : "gray"}>
                {rule.activity ?? "No activity yet"}
              </Text>
            </Table.RowHeaderCell>
            <Table.Cell>
              <Text as="div" style={{ fontVariantNumeric: "tabular-nums" }}>
                {describeFactor(rule)}
              </Text>
              <Text as="div" size="1" color="gray">
                {describeUnit(rule)}
              </Text>
            </Table.Cell>
          </ClickableRow>
        ))}
      </Table.Body>
    </Table.Root>
  );
}
