import type { ClassNode } from "../api/socel";

export interface ClassOption {
  path: string;
  label: string;
  /** How deep the class sits in its tree; roots are 0. */
  depth: number;
}

/** Reconstruct class paths and depths while walking the taxonomy's local names. */
export function classOptions(
  trees: readonly ClassNode[],
  depth = 0,
  parentPath = "",
): ClassOption[] {
  return trees.flatMap((node) => {
    const path = parentPath ? `${parentPath}.${node.label}` : node.label;
    return [
      { path, label: node.label, depth },
      ...classOptions(node.children ?? [], depth + 1, path),
    ];
  });
}

/** The share of all events or objects whose type has a class, from 0 to 1. */
export function classifiedShare(
  types: readonly { name: string; count: number }[],
  classOf: (name: string) => string | null,
) {
  const total = types.reduce((sum, type) => sum + type.count, 0);
  const classified = types.reduce(
    (sum, type) => sum + (classOf(type.name) === null ? 0 : type.count),
    0,
  );
  return total === 0 ? 0 : classified / total;
}
