import { useEffect, useState } from "react";

/** A flow's factors as typed, in kg CO2e per unit flowing into the objects and
 * per unit flowing out of them. */
export interface FactorEntry {
  inflow: string;
  outflow: string;
}

export type Factors = Readonly<Record<string, FactorEntry>>;

// Factors come from outside the log (thesis, Def. 6.4.1) and hold for a flow
// whichever log it is in: they are kept per flow in the browser.
const KEY = "ocean:factors";
const NONE: FactorEntry = { inflow: "", outflow: "" };

const read = (): Factors => {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "{}") as Factors;
  } catch {
    return {};
  }
};

/** The factors entered for the flows, kept across visits. */
export function useFactors() {
  const [factors, setFactors] = useState<Factors>(read);

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(factors));
    } catch {
      // Without storage the factors last until the page is left.
    }
  }, [factors]);

  const change = (flowId: string, entry: Partial<FactorEntry>) =>
    setFactors((current) => ({
      ...current,
      [flowId]: { ...NONE, ...current[flowId], ...entry },
    }));

  return { factors, change };
}
