import { keepPreviousData } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  type DirectionFactors,
  type ImpactAnalysis,
  type ImpactReport as ImpactReportResult,
  useCalculateImpact,
} from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type ImpactReport = ImpactReportResult;
export type Period = NonNullable<ImpactAnalysis["period"]>;

/** The impact of the selected sOCEL's flows with the given factors (kg CO2e per
 * unit into and out of the objects), per flow, in all and per period. Asked again a moment after the
 * factors stop changing, not on every keystroke. */
export function useImpact(
  period: Period,
  factors: Readonly<Record<string, DirectionFactors>>,
) {
  const { ocelId, enabled } = useSelectedOcel();
  const settled = useSettled(factors, 300);
  return useCalculateImpact(ocelId, { period, factors: settled }, undefined, {
    query: { enabled, placeholderData: keepPreviousData },
  });
}

function useSettled<T>(value: T, ms: number) {
  const [settled, setSettled] = useState(value);
  const key = JSON.stringify(value);
  // By the key: a new object with the same factors is no change.
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [key, ms]);
  return settled;
}
