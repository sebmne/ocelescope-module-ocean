import type { AttributeRef } from "../../components/pickers";
import type { EmissionRule, EmissionRuleType } from "./types";

export const ruleTypeLabels: Record<EmissionRuleType, string> = {
  E: "Event",
  E2O: "Event → Object",
};

export function createEmptyRule(id: number): EmissionRule {
  return {
    id,
    type: "E",
    activity: undefined,
    relation: undefined,
    factor: { value: undefined, attributes: [] },
  };
}

/** A rule can be computed once every field its type needs is filled in. */
export function isRuleComplete(rule: EmissionRule): boolean {
  if (!rule.activity || rule.factor.value === undefined) return false;
  if (rule.type === "E2O" && !rule.relation) return false;
  return true;
}

const attributeLabel = (ref: AttributeRef) =>
  ref.target === "event" ? ref.name : `${ref.objectType}.${ref.name}`;

/** The factor as a formula, e.g. "0.27 kg CO₂e × distance × Container.Weight". */
export function describeFactor(rule: EmissionRule): string {
  const value = rule.factor.value === undefined ? "? kg CO₂e" : `${rule.factor.value} kg CO₂e`;
  const per = rule.type === "E2O" ? `per ${rule.relation?.objectType ?? "object"}` : "per event";

  return rule.factor.attributes.length > 0
    ? [value, ...rule.factor.attributes.map(attributeLabel)].join(" × ")
    : `${value} ${per}`;
}
