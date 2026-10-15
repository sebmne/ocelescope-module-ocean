import { useMemo, useState } from "react";
import type { PreparationDraft } from "../../api/socel";
import { useClassTaxonomies } from "../../hooks/useClassTaxonomies";
import { classOptions } from "../../lib/classOptions";
import { type ContainmentDraft, problemOf, typeContainments } from "./containment";
import {
  type AttributeChoices,
  attributeFlows,
  definitions,
  type FlowDrafts,
  newFlows,
} from "./flowDrafts";
import { useEventAttributes } from "./useEventAttributes";
import { canBeRead, useRecordFile } from "./useRecordFile";
import { useTypeRelations } from "./useTypeRelations";

/** The flow part of the changes to a log. */
export type FlowChanges = Pick<
  PreparationDraft,
  "flows" | "records" | "attributeFlows" | "containment"
>;

/**
 * The flows to add to the selected log: from a file and from event attributes,
 * with their definitions and the containment of their instances.
 */
export function useAddFlows() {
  const taxonomies = useClassTaxonomies();
  const records = useRecordFile();
  const attributes = useEventAttributes();
  const { relations } = useTypeRelations();
  const [choices, setChoices] = useState<AttributeChoices>({});
  // Whether attributes are a source of flows, and whether the file's popup
  // opens as its card first shows.
  const [attributesOn, setAttributesOn] = useState(false);
  const [openFile, setOpenFile] = useState(false);
  const [containments, setContainments] = useState<ContainmentDraft[]>([]);
  const [drafts, setDrafts] = useState<FlowDrafts>({});

  const categories = useMemo(
    () => classOptions(taxonomies.data?.flowCategories ?? []),
    [taxonomies.data],
  );
  const flows = newFlows(records.preview, attributes.data ?? [], choices);
  const flowIds = flows.map((flow) => flow.flowId);
  const containment = typeContainments(containments, flowIds);
  const defined = definitions(flowIds, drafts);

  // A containment that is filled in but cannot be used keeps the changes back.
  const badContainments = containments.filter((item) => {
    const problem = problemOf(item, relations, containments);
    return problem !== null && problem !== "Not filled in";
  }).length;
  // A file whose columns are not all told is not taken along silently.
  const fileUnread = !!records.file && !canBeRead(records.mapping);

  const changes: FlowChanges = {
    flows: defined ?? {},
    records:
      records.file && records.preview
        ? { uploadId: records.file.uploadId, mapping: records.mapping }
        : null,
    attributeFlows: attributeFlows(choices),
    containment,
  };

  const reset = () => {
    records.remove();
    setChoices({});
    setAttributesOn(false);
    setOpenFile(false);
    setContainments([]);
    setDrafts({});
  };

  return {
    records,
    choices,
    setChoices,
    attributesOn,
    setAttributesOn,
    openFile,
    setOpenFile,
    containments,
    setContainments,
    drafts,
    define: (flowId: string, draft: FlowDrafts[string]) =>
      setDrafts((current) => ({ ...current, [flowId]: draft })),
    categories,
    flows,
    flowIds,
    changes,
    /** Whether anything would be added. */
    isEmpty: flows.length === 0 && containment.length === 0,
    problems: { undefinedFlows: defined === null, badContainments, fileUnread },
    reset,
  };
}

export type AddFlowsState = ReturnType<typeof useAddFlows>;
