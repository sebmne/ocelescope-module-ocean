import { useState } from "react";
import type { FlowEdit } from "../../api/socel";
import { type Flow, useFlowInventory } from "../../hooks/useFlowInventory";

/** A flow as the page holds it while it is edited. */
export interface FlowDraft {
  name: string;
  unit: string;
  category: string | null;
  externalRef: string;
  /** How many of the new unit one of the old unit is, as typed. */
  conversion: string;
  deleted: boolean;
}

const asDraft = (flow: Flow): FlowDraft => ({
  name: flow.flowId,
  unit: flow.unit,
  category: flow.category,
  externalRef: flow.externalRef ?? "",
  conversion: "",
  deleted: false,
});

const parse = (text: string) => {
  const trimmed = text.trim();
  return trimmed === "" ? Number.NaN : Number(trimmed.replace(",", "."));
};

/** What keeps a flow's edit from being saved; null when it can be. */
export type Problem = "name" | "taken" | "unit" | "conversion";

/**
 * The selected sOCEL's flows with the edits made to them: renamed, given
 * another unit (with the factor its quantities are converted by), category or
 * reference, or deleted.
 */
export function useFlowEdits() {
  const inventory = useFlowInventory();
  const [drafts, setDrafts] = useState<Readonly<Record<string, FlowDraft>>>({});
  const flows = inventory.data ?? [];

  const draftOf = (flow: Flow) => drafts[flow.flowId] ?? asDraft(flow);
  const unitChanged = (flow: Flow) => draftOf(flow).unit.trim() !== flow.unit;
  const isChanged = (flow: Flow) => {
    const draft = draftOf(flow);
    const base = asDraft(flow);
    return (
      draft.deleted ||
      draft.name.trim() !== base.name ||
      unitChanged(flow) ||
      draft.category !== base.category ||
      draft.externalRef.trim() !== base.externalRef
    );
  };

  // Names the flows would have, to find two with the same one.
  const kept = flows.filter((flow) => !draftOf(flow).deleted);
  const names = kept.map((flow) => draftOf(flow).name.trim());
  const problemOf = (flow: Flow): Problem | null => {
    const draft = draftOf(flow);
    if (draft.deleted) return null;
    const name = draft.name.trim();
    if (name === "") return "name";
    if (names.filter((other) => other === name).length > 1) return "taken";
    if (draft.unit.trim() === "") return "unit";
    if (unitChanged(flow)) {
      const factor = parse(draft.conversion);
      if (!Number.isFinite(factor) || factor === 0) return "conversion";
    }
    return null;
  };

  const changed = flows.filter(isChanged);
  const edits: FlowEdit[] = changed.map((flow) => {
    const draft = draftOf(flow);
    return {
      flowId: flow.flowId,
      name: draft.name.trim(),
      unit: draft.unit.trim(),
      category: draft.category,
      externalRef: draft.externalRef.trim() || null,
      conversion: unitChanged(flow) ? parse(draft.conversion) : null,
      delete: draft.deleted,
    };
  });

  return {
    inventory,
    flows,
    draftOf,
    change: (flow: Flow, change: Partial<FlowDraft>) =>
      setDrafts((current) => ({
        ...current,
        [flow.flowId]: { ...(current[flow.flowId] ?? asDraft(flow)), ...change },
      })),
    isChanged,
    unitChanged,
    problemOf,
    edits,
    hasProblems: flows.some((flow) => problemOf(flow) !== null),
    reset: () => setDrafts({}),
  };
}

export type FlowEditsState = ReturnType<typeof useFlowEdits>;
