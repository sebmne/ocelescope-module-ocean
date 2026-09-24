import { useEffect, useRef, useState } from "react";
import { useSaveEmissionRules } from "../../../data/useSaveEmissionRules";
import { useSelectedOcel } from "../../../data/useSelectedOcel";
import { useStoredEmissionRules } from "../../../data/useStoredEmissionRules";
import { createEmptyRule, type EmissionRuleDraft } from "../../../model/emissionRules";

const SAVE_DELAY_MS = 500;

interface Editing {
  ocelId: string;
  rules: EmissionRuleDraft[];
}

// The rules of the selected OCEL, as the user edits them. They are loaded from
// the session and every change is saved back after a short pause.
export function useEmissionRules() {
  const { id: ocelId } = useSelectedOcel();
  const stored = useStoredEmissionRules();
  const { save, error } = useSaveEmissionRules();

  const [editing, setEditing] = useState<Editing | null>(null);

  // Take over the stored rules when an OCEL is selected (or another one).
  if (ocelId && stored.data && editing?.ocelId !== ocelId) {
    setEditing({ ocelId, rules: stored.data });
  }

  // Unsaved changes, and the latest state, for the effects below.
  const unsaved = useRef(false);
  const latest = useRef(editing);
  latest.current = editing;
  const saveRef = useRef(save);
  saveRef.current = save;

  // Save after a pause in editing.
  useEffect(() => {
    if (!editing || !unsaved.current) return;
    const timer = setTimeout(() => {
      saveRef.current(editing.ocelId, editing.rules);
      unsaved.current = false;
    }, SAVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [editing]);

  // Save right away when the OCEL changes or the page is left, so no change is lost.
  const editingOcel = editing?.ocelId;
  useEffect(
    () => () => {
      if (unsaved.current && latest.current) {
        saveRef.current(latest.current.ocelId, latest.current.rules);
        unsaved.current = false;
      }
    },
    [editingOcel],
  );

  const change = (update: (rules: EmissionRuleDraft[]) => EmissionRuleDraft[]) => {
    unsaved.current = true;
    setEditing((current) => (current ? { ...current, rules: update(current.rules) } : current));
  };

  const addRule = () => {
    const id = crypto.randomUUID();
    change((rules) => [...rules, createEmptyRule(id)]);
    return id;
  };

  const updateRule = (id: string, changes: Partial<EmissionRuleDraft>) =>
    change((rules) => rules.map((r) => (r.id === id ? { ...r, ...changes } : r)));

  const removeRule = (id: string) => change((rules) => rules.filter((r) => r.id !== id));

  // Loading until the stored rules of the selected OCEL are taken over.
  const isLoading = editing === null || editing.ocelId !== ocelId;

  return [editing?.rules ?? [], addRule, updateRule, removeRule, error, isLoading] as const;
}
