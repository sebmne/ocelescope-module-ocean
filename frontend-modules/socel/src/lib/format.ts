// Masses are computed in kg; shown in the unit that keeps the number short.
const massUnits = [
  { unit: "Mt", kg: 1e9 },
  { unit: "kt", kg: 1e6 },
  { unit: "t", kg: 1e3 },
  { unit: "kg", kg: 1 },
  { unit: "g", kg: 1e-3 },
] as const;

/** A mass split into number and unit, e.g. { value: "107", unit: "t" }; "–" when there is none. */
export function massParts(kg: number | null | undefined) {
  if (kg == null) return { value: "–", unit: "" };
  if (kg === 0) return { value: "0", unit: "kg" };

  const { unit, kg: perUnit } =
    massUnits.find((candidate) => Math.abs(kg) >= candidate.kg) ?? massUnits[massUnits.length - 1];
  const scaled = kg / perUnit;
  const value = scaled.toLocaleString(undefined, {
    maximumFractionDigits: Math.abs(scaled) < 10 ? 2 : Math.abs(scaled) < 100 ? 1 : 0,
  });
  return { value, unit };
}

/** A mass for display, e.g. "107 t"; "–" when there is none. */
export function formatMass(kg: number | null | undefined) {
  const { value, unit } = massParts(kg);
  return unit ? `${value} ${unit}` : value;
}

/** An amount of emissions for display, e.g. "107 t CO₂e"; "–" when there is none. */
export function formatCo2e(kg: number | null | undefined) {
  return kg == null ? "–" : `${formatMass(kg)} CO₂e`;
}

/** A share of a whole, e.g. "93 %"; undefined when the whole is empty. */
export function formatShare(part: number | null | undefined, whole: number | null | undefined) {
  if (part == null || !whole) return undefined;
  return (part / whole).toLocaleString(undefined, { style: "percent", maximumFractionDigits: 0 });
}

/** A mass in kg, unscaled, e.g. "107,400.5 kg CO₂e". */
export function formatExactKg(kg: number) {
  return `${kg.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg CO₂e`;
}

export function formatCount(count: number) {
  return count.toLocaleString();
}
