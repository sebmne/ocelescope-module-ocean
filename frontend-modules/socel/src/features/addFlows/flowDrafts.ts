import type {
  AttributeFlow,
  FlowDefinition,
  RecordFilePreview,
} from "../../api/socel";
import type { EventAttribute } from "./useEventAttributes";

/** What neither a file nor an attribute knows about a flow; empty until set. */
export interface FlowDraft {
  unit: string;
  category: string | null;
  /** Where the flow is described elsewhere, e.g. a link; may stay empty. */
  externalRef: string;
}
export type FlowDrafts = Readonly<Record<string, FlowDraft>>;
export const EMPTY_DRAFT: FlowDraft = { unit: "", category: null, externalRef: "" };

/** An event attribute chosen as a flow: the flow's name, the type of object it
 * is observed at, and whether its amounts flow into that object or out of it. */
export interface AttributeChoice {
  flowId: string;
  objectType: string;
  direction: "in" | "out";
}
export type AttributeChoices = Readonly<Record<string, AttributeChoice>>;

/** One flow the new sOCEL gets, with where its records come from. The counts
 * are those of the file; an attribute gives one record per event that has a
 * value. */
export interface NewFlow {
  flowId: string;
  intervalRecords: number;
  eventRecords: number;
  fromFile: boolean;
  attributes: readonly string[];
}

/** The flows the build would bring: those of the file that have usable rows,
 * and those of the chosen attributes. */
export function newFlows(
  preview: RecordFilePreview | null | undefined,
  attributes: readonly EventAttribute[],
  choices: AttributeChoices,
): NewFlow[] {
  const flows = new Map<string, NewFlow>();
  const flow = (flowId: string) => {
    const existing = flows.get(flowId);
    if (existing) return existing;
    const added: NewFlow = {
      flowId,
      intervalRecords: 0,
      eventRecords: 0,
      fromFile: false,
      attributes: [],
    };
    flows.set(flowId, added);
    return added;
  };
  for (const inFile of preview?.flows ?? []) {
    if (inFile.usableRows === 0) continue;
    Object.assign(flow(inFile.flowId), {
      intervalRecords: inFile.intervalRecords,
      eventRecords: inFile.eventRecords,
      fromFile: true,
    });
  }
  for (const attribute of attributes) {
    const choice = choices[attribute.name];
    if (!choice || choice.flowId.trim() === "") continue;
    const target = flow(choice.flowId.trim());
    Object.assign(target, { attributes: [...target.attributes, attribute.name] });
  }
  return [...flows.values()];
}

/** The definitions of the given flows as the build needs them; null while a
 * flow lacks its unit or category. */
export function definitions(flowIds: readonly string[], drafts: FlowDrafts) {
  const defined: Record<string, FlowDefinition> = {};
  for (const flowId of flowIds) {
    const draft = drafts[flowId] ?? EMPTY_DRAFT;
    const unit = draft.unit.trim();
    const category = draft.category;
    if (unit === "" || category === null) return null;
    defined[flowId] = {
      unit,
      category,
      externalRef: draft.externalRef.trim() || null,
    };
  }
  return defined;
}

/** The chosen attributes as the build needs them. */
export function attributeFlows(choices: AttributeChoices): AttributeFlow[] {
  return Object.entries(choices)
    .filter(([, choice]) => choice.flowId.trim() !== "")
    .map(([attribute, choice]) => ({
      attribute,
      flowId: choice.flowId.trim(),
      objectType: choice.objectType,
      direction: choice.direction,
    }));
}
