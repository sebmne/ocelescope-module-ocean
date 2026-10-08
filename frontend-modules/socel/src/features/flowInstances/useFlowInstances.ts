import { keepPreviousData } from "@tanstack/react-query";
import { type FlowInstanceModel, useGetFlowInstances } from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type FlowInstance = FlowInstanceModel;
export type InstanceOrder = "quantity" | "object";

export const PAGE_SIZE = 25;

interface Filter {
  objectType: string | null;
  inside: string | null;
  search: string;
  order: InstanceOrder;
  page: number;
}

/** One page of the objects a flow is observed at. While the next page loads, the
 * one before stays, so the table does not blink. */
export function useFlowInstances(flowId: string, filter: Filter) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowInstances(
    ocelId,
    flowId,
    {
      object_type: filter.objectType,
      inside: filter.inside,
      search: filter.search.trim() || null,
      order: filter.order,
      offset: filter.page * PAGE_SIZE,
      limit: PAGE_SIZE,
    },
    { query: { enabled, placeholderData: keepPreviousData } },
  );
}
