// How the computed emissions are distributed to objects, as the page holds it.
// Pure data and functions - no API types, no React.

/** How event emissions are distributed to the target objects. */
export type AllocationRule = "AllTargets" | "ParticipatingTargets" | "ClosestTargets";

export interface AllocationConfig {
  targetObjectTypes: string[];
  rule: AllocationRule;
  /** Also pass emissions via resource objects. */
  passViaResources: boolean;
  /** Pass emissions between objects of the same type. */
  passBetweenSameType: boolean;
}

export const defaultAllocationConfig: AllocationConfig = {
  targetObjectTypes: [],
  rule: "ParticipatingTargets",
  passViaResources: false,
  passBetweenSameType: true,
};

/** Why allocating is not possible yet, or undefined if it is. */
export function allocationBlocker(config: AllocationConfig, emissionsComputed: boolean) {
  if (!emissionsComputed) return "Compute emissions first.";
  if (config.targetObjectTypes.length === 0) return "Choose target object types.";
  return undefined;
}

/** Whether two configurations allocate the same way. */
export function sameAllocationConfig(a: AllocationConfig, b: AllocationConfig) {
  return (
    a.rule === b.rule &&
    a.passViaResources === b.passViaResources &&
    a.passBetweenSameType === b.passBetweenSameType &&
    [...a.targetObjectTypes].sort().join("\n") === [...b.targetObjectTypes].sort().join("\n")
  );
}
