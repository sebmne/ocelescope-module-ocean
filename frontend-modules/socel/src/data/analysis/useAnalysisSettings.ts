import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  type AnalysisSettingsModel,
  type ChoiceModel,
  getGetAllocationQueryKey,
  getGetAnalysisSettingsQueryKey,
  getGetAttributionQueryKey,
  getGetImpactQueryKey,
  useGetAnalysisSettings,
  useSaveAnalysisSettings,
} from "../../api/socel";
import { errorMessage } from "../errorMessage";
import { useSelectedOcel } from "../useSelectedOcel";

export interface EmissionFactor {
  flowId: string;
  /** kg CO₂e per unit of the flow. */
  impactPerUnit: number;
}

/** What the analyst decides, as the page edits it. */
export interface AnalysisSettings {
  groupMetering: boolean;
  createdFromQualifier: string | null;
  massAttribute: string | null;
  emissionFactors: EmissionFactor[];
}

export type SettingChoice = ChoiceModel;

const SAVE_DELAY_MS = 500;

const normalized = (stored: AnalysisSettingsModel): AnalysisSettings => ({
  groupMetering: stored.groupMetering ?? true,
  createdFromQualifier: stored.createdFromQualifier ?? null,
  massAttribute: stored.massAttribute ?? null,
  emissionFactors: stored.emissionFactors ?? [],
});

interface Editing {
  ocelId: string;
  settings: AnalysisSettings;
}

/**
 * The analysis settings of the selected OCEL, and what it offers for them. Every
 * change is saved to the session after a short pause (factors are typed), and
 * the results that depend on the settings are fetched again.
 */
export function useAnalysisSettings() {
  const { id: ocelId, ocelId: key, enabled } = useSelectedOcel();
  const stored = useGetAnalysisSettings(key, undefined, { query: { enabled } });
  const queryClient = useQueryClient();
  const mutation = useSaveAnalysisSettings({
    mutation: {
      onSuccess: (saved, { ocelId: savedFor }) => {
        queryClient.setQueryData(
          getGetAnalysisSettingsQueryKey(savedFor),
          (view: typeof stored.data) => view && { ...view, settings: saved },
        );
        for (const queryKey of [
          getGetAttributionQueryKey(savedFor),
          getGetAllocationQueryKey(savedFor),
          getGetImpactQueryKey(savedFor),
        ]) {
          queryClient.invalidateQueries({ queryKey });
        }
      },
    },
  });

  const [editing, setEditing] = useState<Editing | null>(null);
  if (ocelId && stored.data && editing?.ocelId !== ocelId) {
    setEditing({ ocelId, settings: normalized(stored.data.settings) });
  }

  const unsaved = useRef(false);
  const saveRef = useRef(mutation.mutate);
  saveRef.current = mutation.mutate;

  useEffect(() => {
    if (!editing || !unsaved.current) return;
    const timer = setTimeout(() => {
      saveRef.current({ ocelId: editing.ocelId, data: editing.settings });
      unsaved.current = false;
    }, SAVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [editing]);

  const update = (changes: Partial<AnalysisSettings>) => {
    unsaved.current = true;
    setEditing((current) =>
      current ? { ...current, settings: { ...current.settings, ...changes } } : current,
    );
  };

  return {
    settings: editing?.ocelId === ocelId ? editing.settings : undefined,
    createdFromQualifiers: stored.data?.createdFromQualifiers ?? [],
    massAttributes: stored.data?.massAttributes ?? [],
    update,
    isSaving: mutation.isPending || unsaved.current,
    error: errorMessage(mutation.error, "Saving the analysis settings failed."),
  };
}
