// The emission rules as the editor holds them: drafts that may still be
// incomplete while the user fills them in. Pure data and functions - no API
// types, no React.
import type { AttributeRef, E2ORelation } from "../components/pickers";

/** E: emissions per event. E2O: emissions per event-to-object relation. */
export type EmissionRuleType = "E" | "E2O";

/** A constant emission value, multiplied by the values of the selected attributes. */
export interface EmissionFactorDraft {
  /** kg CO₂e per event (or relation), or per unit of the selected attributes. */
  value: number | undefined;
  attributes: AttributeRef[];
}

export interface EmissionRuleDraft {
  /** Stable across saves and reloads. */
  id: string;
  type: EmissionRuleType;
  activity: string | undefined;
  /** Only used by E2O rules: which related objects receive the emissions. */
  relation: E2ORelation | undefined;
  factor: EmissionFactorDraft;
}

export function createEmptyRule(id: string): EmissionRuleDraft {
  return {
    id,
    type: "E",
    activity: undefined,
    relation: undefined,
    factor: { value: undefined, attributes: [] },
  };
}

/** A rule can be computed once every field its type needs is filled in. */
export function isRuleComplete(rule: EmissionRuleDraft): boolean {
  if (!rule.activity || rule.factor.value === undefined) return false;
  if (rule.type === "E2O" && !rule.relation) return false;
  return true;
}

export const attributeLabel = (ref: AttributeRef) =>
  ref.target === "event" ? ref.name : `${ref.objectType}.${ref.name}`;

/** The factor's value, e.g. "0.27 kg CO₂e", or undefined while it is missing. */
export function describeValue(rule: EmissionRuleDraft): string | undefined {
  return rule.factor.value === undefined
    ? undefined
    : `${rule.factor.value.toLocaleString()} kg CO₂e`;
}

/** The factor as a formula, e.g. "0.27 kg CO₂e × distance × Container.Weight". */
export function describeFactor(rule: EmissionRuleDraft): string {
  return [describeValue(rule) ?? "? kg CO₂e", ...rule.factor.attributes.map(attributeLabel)].join(
    " × ",
  );
}

/** What one emission is counted for, e.g. "per event" or "per related Truck". */
export function describeUnit(rule: EmissionRuleDraft): string {
  if (rule.type === "E") return "per event";
  if (!rule.relation) return "per related object";
  const { objectType, qualifier } = rule.relation;
  return qualifier ? `per related ${objectType} (${qualifier})` : `per related ${objectType}`;
}

/**
 * The factor's attributes that still fit after a change: the event attributes,
 * plus object attributes of `objectType` if given.
 */
export function attributesFor(rule: EmissionRuleDraft, objectType: string | undefined) {
  return rule.factor.attributes.filter(
    (ref) => ref.target === "event" || ref.objectType === objectType,
  );
}
