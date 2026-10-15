import type { ClassCount } from "../../api/socel";

export interface TaxonomyNode {
  /** The class path up to this node, e.g. "root.branch"; null for unclassified. */
  path: string | null;
  /** The last segment of the path, e.g. "branch". */
  label: string;
  /** Entities carrying exactly this class. */
  own: number;
  /** Entities carrying this class or one below it. */
  total: number;
  children: TaxonomyNode[];
}

/**
 * The classes as a taxonomy tree, by their dot-separated segments:
 * "root.branch.leaf" lies below "root.branch", below "root". The tree is
 * reconstructed from the paths assigned in the log. Siblings are ordered by
 * total, largest first; unclassified entities come last, as a root of their own.
 */
export function taxonomyTree(classes: readonly ClassCount[]): TaxonomyNode[] {
  const roots: TaxonomyNode[] = [];
  let unclassified: TaxonomyNode | undefined;

  for (const { socelClass, count } of classes) {
    if (socelClass === null) {
      unclassified = {
        path: null,
        label: "unclassified",
        own: count,
        total: count,
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
        node = { path, label: segment, own: 0, total: 0, children: [] };
        level.push(node);
      }
      node.total += count;
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
