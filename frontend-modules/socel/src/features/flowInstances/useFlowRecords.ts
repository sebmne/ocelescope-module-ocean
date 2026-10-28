import { keepPreviousData } from "@tanstack/react-query";
import { type FlowRecord as ApiFlowRecord, useGetFlowRecords } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type FlowRecord = ApiFlowRecord;

export const RECORD_PAGE_SIZE = 50;

/** One page of a flow's records at one object, earliest first. */
export function useFlowRecords(flowId: string, objectId: string, page: number) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowRecords(
    ocelId,
    flowId,
    { object_id: objectId, offset: page * RECORD_PAGE_SIZE, limit: RECORD_PAGE_SIZE },
    { query: { enabled, placeholderData: keepPreviousData } },
  );
}
