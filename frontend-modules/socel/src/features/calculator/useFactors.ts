import { useState } from "react";

/** A flow's factors as typed, in kg CO2e per unit flowing into the objects and
 * per unit flowing out of them. */
export interface FactorEntry {
  inflow: string;
  outflow: string;
}

export type Factors = Readonly<Record<string, FactorEntry>>;

const NONE: FactorEntry = { inflow: "", outflow: "" };

export function useFactors() {
  const [factors, setFactors] = useState<Factors>({});

  const change = (flowId: string, entry: Partial<FactorEntry>) =>
    setFactors((current) => ({
      ...current,
      [flowId]: { ...NONE, ...current[flowId], ...entry },
    }));

  return { factors, change };
}
