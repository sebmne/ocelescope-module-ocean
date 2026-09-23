// Data model of the Emissions page. Mirrors the OCEAn backend models, so it
// can be mapped to the generated API types once the backend exists.
import type { AttributeRef, E2ORelation } from "../../components/pickers";

/** E: emissions per event. E2O: emissions per event-to-object relation. */
export type EmissionRuleType = "E" | "E2O";

/** A constant emission value, multiplied by the values of the selected attributes. */
export interface EmissionFactor {
  /** kg CO₂e per event (or relation), or per unit of the selected attributes. */
  value: number | undefined;
  attributes: AttributeRef[];
}

export interface EmissionRule {
  id: number;
  type: EmissionRuleType;
  activity: string | undefined;
  /** Only used by E2O rules: which related objects receive the emissions. */
  relation: E2ORelation | undefined;
  factor: EmissionFactor;
}

/** How event emissions are distributed to the target objects. */
export type AllocationRule = "AllTargets" | "ParticipatingTargets" | "ClosestTargets";

export interface AllocationConfig {
  targetObjectTypes: string[];
  rule: AllocationRule;
  /** Also pass emissions via resource objects (backend: graph_mode "HU"). */
  passViaResources: boolean;
  /** Pass emissions between objects of the same type (backend: remove_otype_loops false). */
  passBetweenSameType: boolean;
}
