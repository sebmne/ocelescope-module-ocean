/** A flow instance as the scope tree needs it: its object and where it reports within. */
export interface ScopedInstance {
  objectId: string;
  parentObjectId: string | null;
}

export interface ScopeNode<T extends ScopedInstance> {
  instance: T;
  children: ScopeNode<T>[];
}

/**
 * The flow instances of one flow as a forest of metering scopes: each root is an
 * instance contained in no other, its children the instances reporting within it.
 * Containment is acyclic (V9); an instance whose parent is missing becomes a root.
 */
export function scopeTree<T extends ScopedInstance>(instances: readonly T[]): ScopeNode<T>[] {
  const nodes = new Map(
    instances.map((instance) => [instance.objectId, { instance, children: [] as ScopeNode<T>[] }]),
  );
  const roots: ScopeNode<T>[] = [];
  for (const node of nodes.values()) {
    const parent = node.instance.parentObjectId && nodes.get(node.instance.parentObjectId);
    (parent ? parent.children : roots).push(node);
  }
  return roots;
}
