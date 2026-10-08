export interface ClassTree {
  path: string;
  label: string;
  children: readonly ClassTree[];
}

export interface ClassOption {
  path: string;
  label: string;
  /** How deep the class sits in its tree; roots are 0. */
  depth: number;
}

/** A taxonomy's classes in reading order, each knowing its depth. */
export function classOptions(trees: readonly ClassTree[], depth = 0): ClassOption[] {
  return trees.flatMap((node) => [
    { path: node.path, label: node.label, depth },
    ...classOptions(node.children, depth + 1),
  ]);
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
