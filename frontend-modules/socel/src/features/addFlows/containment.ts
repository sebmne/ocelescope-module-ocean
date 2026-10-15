import type { TypeContainment } from "../../api/socel";

/** An object-to-object relation between two object types: from `source` to
 * `target` under `qualifier`, how many pairs it has, and the most targets one
 * object of the source type has. */
export interface TypeRelation {
  source: string;
  target: string;
  qualifier: string;
  pairs: number;
  mostPerObject: number;
}

/** One object type inside another as the page holds it, possibly not filled in yet. */
export interface ContainmentDraft {
  id: number;
  objectType: string | null;
  parentType: string | null;
  qualifier: string | null;
  flows: readonly string[];
}

/** What keeps a containment from being used; null when it can be. */
export function problemOf(
  containment: ContainmentDraft,
  relations: readonly TypeRelation[],
  containments: readonly ContainmentDraft[],
): string | null {
  if (!containment.objectType || !containment.parentType || !containment.qualifier)
    return "Not filled in";
  if (containment.flows.length === 0) return "No flow chosen";
  const relation = relations.find(
    (candidate) =>
      candidate.source === containment.objectType &&
      candidate.target === containment.parentType &&
      candidate.qualifier === containment.qualifier,
  );
  if (relation && relation.mostPerObject > 1) {
    return `A ${containment.objectType} can have ${relation.mostPerObject} ${containment.parentType}s here, but it lies inside one at most`;
  }
  const twice = containments.some(
    (other) =>
      other.id !== containment.id &&
      other.objectType === containment.objectType &&
      other.flows.some((flow) => containment.flows.includes(flow)),
  );
  if (twice)
    return `${containment.objectType} lies inside another type already for one of these flows`;
  return null;
}

/** The containments as the build needs them, for the flows that still exist. */
export function typeContainments(
  containments: readonly ContainmentDraft[],
  flows: readonly string[],
): TypeContainment[] {
  return containments.flatMap((containment) => {
    const kept = containment.flows.filter((flow) => flows.includes(flow));
    return containment.objectType &&
      containment.parentType &&
      containment.qualifier &&
      kept.length > 0
      ? [
          {
            objectType: containment.objectType,
            parentType: containment.parentType,
            qualifier: containment.qualifier,
            flows: kept,
          },
        ]
      : [];
  });
}

/** For one flow, the object types from the outermost inwards, each with how
 * deep it lies: the picture of what lies inside what. */
export function nesting(containments: readonly ContainmentDraft[], flow: string) {
  const parentOf = new Map<string, string>();
  for (const containment of containments) {
    if (containment.objectType && containment.parentType && containment.flows.includes(flow)) {
      parentOf.set(containment.objectType, containment.parentType);
    }
  }
  const childrenOf = new Map<string, string[]>();
  for (const [child, parent] of parentOf) {
    childrenOf.set(parent, [...(childrenOf.get(parent) ?? []), child]);
  }
  const roots = [...childrenOf.keys()].filter((type) => !parentOf.has(type)).toSorted();
  const lines: { type: string; depth: number }[] = [];
  const visit = (type: string, depth: number) => {
    // A cycle would never end; the log's validation reports it.
    if (depth > 20) return;
    lines.push({ type, depth });
    for (const child of (childrenOf.get(type) ?? []).toSorted()) visit(child, depth + 1);
  };
  for (const root of roots) visit(root, 0);
  return lines;
}
