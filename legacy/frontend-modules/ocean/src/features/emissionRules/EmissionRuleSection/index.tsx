import { ListChecksIcon, PlusIcon, Trash2Icon } from "lucide-react";
import { useState } from "react";
import { useComputeEmissions } from "../../../data/useComputeEmissions";
import { useEmissionsOverview } from "../../../data/useEmissionsOverview";
import {
  Button,
  EmptyState,
  Flex,
  Notice,
  Section,
  SideSheet,
  Spinner,
  type Status,
} from "../../../ui";
import RuleEditor from "./RuleEditor";
import RuleTable from "./RuleTable";
import { useEmissionRules } from "./useEmissionRules";

interface EmissionRuleSectionProps {
  /** The section's place in the page's workflow. */
  step: number;
}

// The rules, their editor, and computing their emissions.
export default function EmissionRuleSection({ step }: EmissionRuleSectionProps) {
  const [rules, onAdd, onChange, onRemove, saveError, isLoading] = useEmissionRules();

  // The rule open in the side sheet. Only this section cares, so the state lives here.
  const [editingId, setEditingId] = useState<string | null>(null);
  const editingRule = rules.find((rule) => rule.id === editingId);
  const addRule = () => setEditingId(onAdd());

  const computation = useComputeEmissions(rules);
  const computed = useEmissionsOverview().data?.totalKg != null;

  const status: Status = computation.isPending
    ? { tone: "busy", label: "Computing" }
    : computation.isOutdated
      ? { tone: "attention", label: "Rules changed" }
      : computed
        ? { tone: "done", label: "Computed" }
        : { tone: "idle", label: "Not computed" };

  return (
    <Section
      step={step}
      title="Emission rules"
      status={status}
      actions={
        !isLoading &&
        rules.length > 0 && (
          <Button variant="soft" onClick={addRule}>
            <PlusIcon size={15} aria-hidden /> Add rule
          </Button>
        )
      }
      footer={
        <Flex justify="end" align="center" gap="3" wrap="wrap">
          <Button
            onClick={computation.compute}
            disabled={!computation.canCompute}
            loading={computation.isPending}
            variant={status.tone === "done" ? "soft" : "solid"}
          >
            {computed ? "Recompute emissions" : "Compute emissions"}
          </Button>
        </Flex>
      }
    >
      {isLoading ? (
        <Flex justify="center" py="6">
          <Spinner size="3" />
        </Flex>
      ) : rules.length === 0 ? (
        <EmptyState
          icon={ListChecksIcon}
          title="No emission rules yet"
          action={
            <Button onClick={addRule}>
              <PlusIcon size={15} aria-hidden /> Add the first rule
            </Button>
          }
        />
      ) : (
        <RuleTable rules={rules} onEdit={setEditingId} onRemove={onRemove} />
      )}

      {computation.error && <Notice tone="error">{computation.error}</Notice>}
      {saveError && <Notice tone="error">{saveError}</Notice>}

      <SideSheet
        open={editingRule !== undefined}
        onClose={() => setEditingId(null)}
        title="Edit rule"
        footer={
          editingRule && (
            <Flex justify="between">
              <Button
                variant="ghost"
                color="red"
                onClick={() => {
                  onRemove(editingRule.id);
                  setEditingId(null);
                }}
              >
                <Trash2Icon size={15} aria-hidden /> Delete rule
              </Button>
              <Button onClick={() => setEditingId(null)}>Done</Button>
            </Flex>
          )
        }
      >
        {editingRule && (
          <RuleEditor
            rule={editingRule}
            onChange={(changes) => onChange(editingRule.id, changes)}
          />
        )}
      </SideSheet>
    </Section>
  );
}
