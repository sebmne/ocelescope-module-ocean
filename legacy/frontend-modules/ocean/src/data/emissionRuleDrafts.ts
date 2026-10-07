// Converting rules between the editor's model and the API's shape.
import type { EmissionRuleDraftModel } from "../api/ocean";
import type { EmissionRuleDraft } from "../model/emissionRules";

export function draftFromApi(rule: EmissionRuleDraftModel): EmissionRuleDraft {
  const activity = rule.activity ?? undefined;
  return {
    id: rule.id,
    type: rule.type,
    activity,
    relation: rule.relation
      ? { objectType: rule.relation.objectType, qualifier: rule.relation.qualifier ?? "" }
      : undefined,
    factor: {
      value: rule.factor.value ?? undefined,
      attributes: (rule.factor.attributes ?? []).map((ref) =>
        ref.target === "event"
          ? { target: "event" as const, activity: activity ?? "", name: ref.name }
          : { target: "object" as const, objectType: ref.objectType, name: ref.name },
      ),
    },
  };
}

export function draftToApi(rule: EmissionRuleDraft): EmissionRuleDraftModel {
  return {
    id: rule.id,
    type: rule.type,
    activity: rule.activity ?? null,
    relation: rule.relation
      ? { objectType: rule.relation.objectType, qualifier: rule.relation.qualifier || null }
      : null,
    factor: {
      value: rule.factor.value ?? null,
      attributes: rule.factor.attributes.map((ref) =>
        ref.target === "event"
          ? { target: "event" as const, name: ref.name }
          : { target: "object" as const, objectType: ref.objectType, name: ref.name },
      ),
    },
  };
}
