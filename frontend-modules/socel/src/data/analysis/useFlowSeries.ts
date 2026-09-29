import { type GetFlowSeriesBucket, useGetFlowSeries } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

export type Bucket = GetFlowSeriesBucket;

/** A flow of the selected sOCEL per window of the bucket's length. */
export function useFlowSeries(flowId: string | undefined, bucket: Bucket) {
  const { ocelId, enabled } = useSelectedOcel();
  return useGetFlowSeries(
    ocelId,
    flowId ?? "",
    { bucket },
    { query: { enabled: enabled && flowId !== undefined } },
  );
}
