/** A socel_class with how many objects or events carry it (null: unclassified). */
export interface CountedClass {
  socelClass: string | null;
  count: number;
  /** Makes handling units (objects) or operations (events). */
  isCore: boolean;
}

export interface TaxonomyNode {
  /** The class path up to this node, e.g. "op.manufacturing"; null for unclassified. */
  path: string | null;
  /** The last segment of the path, e.g. "manufacturing". */
  label: string;
  /** Entities carrying exactly this class. */
  own: number;
  /** Entities carrying this class or one below it. */
  total: number;
  isCore: boolean;
  children: TaxonomyNode[];
}

/**
 * The classes as a taxonomy tree, by their dot-separated segments (Chapter 4):
 * "op.manufacturing.forming" lies below "op.manufacturing", below "op". Classes
 * are free text, so the tree is the one the data spans. Siblings are ordered by
 * total, largest first; unclassified entities come last, as a root of their own.
 */
export function taxonomyTree(classes: readonly CountedClass[]): TaxonomyNode[] {
  const roots: TaxonomyNode[] = [];
  let unclassified: TaxonomyNode | undefined;

  for (const { socelClass, count, isCore } of classes) {
    if (socelClass === null) {
      unclassified = {
        path: null,
        label: "unclassified",
        own: count,
        total: count,
        isCore: false,
        children: [],
      };
      continue;
    }
    let level = roots;
    const segments = socelClass.split(".");
    segments.forEach((segment, index) => {
      const path = segments.slice(0, index + 1).join(".");
      let node = level.find((candidate) => candidate.path === path);
      if (!node) {
        node = { path, label: segment, own: 0, total: 0, isCore: false, children: [] };
        level.push(node);
      }
      node.total += count;
      node.isCore ||= isCore;
      if (index === segments.length - 1) node.own += count;
      level = node.children;
    });
  }

  const sort = (nodes: TaxonomyNode[]) => {
    nodes.sort((a, b) => b.total - a.total || a.label.localeCompare(b.label));
    for (const node of nodes) sort(node.children);
  };
  sort(roots);
  return unclassified ? [...roots, unclassified] : roots;
}
