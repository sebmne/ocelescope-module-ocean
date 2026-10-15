import type { DirectionFactors } from "../../api/socel";
import type { Factors } from "./useFactors";

/** A typed factor as a number: null when none is given, NaN when it is no number. */
export const parseFactor = (text: string | undefined) => {
  const trimmed = (text ?? "").trim();
  return trimmed === "" ? null : Number(trimmed.replace(",", "."));
};

const usable = (text: string | undefined) => {
  const factor = parseFactor(text);
  return factor !== null && Number.isFinite(factor) ? factor : undefined;
};

/** The factors that are numbers, by flow and direction: what the impact is
 * calculated with. */
export const usableFactors = (factors: Factors): Record<string, DirectionFactors> =>
  Object.fromEntries(
    Object.entries(factors).flatMap(([flowId, entry]) => {
      const inflow = usable(entry.inflow);
      const outflow = usable(entry.outflow);
      return inflow === undefined && outflow === undefined ? [] : [[flowId, { inflow, outflow }]];
    }),
  );
