import { useState } from "react";
import {
  type FlowInFileModel,
  type RecordIssueModel,
  type UploadedRecordFileModel,
  useUploadRecordFile,
} from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type RecordFile = UploadedRecordFileModel;
export type FlowInFile = FlowInFileModel;
export type RecordIssue = RecordIssueModel;

/** What the file cannot know about a flow; empty until the user sets it. */
export interface FlowDraft {
  unit: string;
  category: string | null;
  /** Where the flow is described elsewhere, e.g. a link; may stay empty. */
  externalRef: string;
}
export type FlowDrafts = Readonly<Record<string, FlowDraft>>;
export const EMPTY_DRAFT: FlowDraft = { unit: "", category: null, externalRef: "" };

/**
 * The record file uploaded for the selected log, and what the user gives each of
 * its flows: unit, category and, if wanted, a reference. A flow the log already
 * has starts with its own.
 */
export function useRecordFile() {
  const { ocelId } = useSelectedOcel();
  const request = useUploadRecordFile<Error>();
  const [file, setFile] = useState<RecordFile>();
  const [flows, setFlows] = useState<FlowDrafts>({});

  const upload = (chosen: File) =>
    request.mutate(
      { ocelId, data: { file: chosen } },
      {
        onSuccess: (uploaded) => {
          setFile(uploaded);
          setFlows(
            Object.fromEntries(
              uploaded.flows.map((flow) => [
                flow.flowId,
                {
                  unit: flow.known?.unit ?? "",
                  category: flow.known?.category ?? null,
                  externalRef: flow.known?.externalRef ?? "",
                },
              ]),
            ),
          );
        },
      },
    );

  const define = (flowId: string, change: Partial<FlowDraft>) =>
    setFlows((current) => ({ ...current, [flowId]: { ...current[flowId], ...change } }));

  return { file, flows, upload, define, isUploading: request.isPending, error: request.error };
}

/** The flows that bring records, as the build needs them; null while one of
 * them still lacks its unit or category. */
export function definedFlows(file: RecordFile, drafts: FlowDrafts) {
  const defined: Record<string, { unit: string; category: string; externalRef: string | null }> =
    {};
  for (const flow of file.flows) {
    if (flow.usableRows === 0) continue;
    const { unit, category, externalRef } = drafts[flow.flowId] ?? EMPTY_DRAFT;
    if (unit.trim() === "" || category === null) return null;
    defined[flow.flowId] = {
      unit: unit.trim(),
      category,
      externalRef: externalRef.trim() || null,
    };
  }
  return defined;
}
