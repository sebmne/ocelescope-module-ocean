import { useState } from "react";
import { useSelectedOcel } from "../../../data/useSelectedOcel";
import { type AllocationConfig, defaultAllocationConfig } from "../../../model/allocation";

interface Editing {
  ocelId: string;
  config: AllocationConfig;
}

// The allocation settings of the selected OCEL, as the user edits them. They
// start as the settings of the stored allocation, so the page shows how the
// result it shows was made; without one, as the defaults.
export function useAllocationConfig(stored: AllocationConfig | null | undefined, loaded: boolean) {
  const { id: ocelId } = useSelectedOcel();
  const [editing, setEditing] = useState<Editing | null>(null);

  // Take over the stored settings once they are loaded for a (new) OCEL.
  if (ocelId && loaded && editing?.ocelId !== ocelId) {
    setEditing({ ocelId, config: stored ?? defaultAllocationConfig });
  }

  const config = editing?.config ?? defaultAllocationConfig;
  const update = (changes: Partial<AllocationConfig>) =>
    setEditing((current) => current && { ...current, config: { ...current.config, ...changes } });

  return [config, update] as const;
}
