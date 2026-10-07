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

/** A length of time in its largest fitting unit, e.g. "3 d", "1 h", "45 min". */
export function formatDuration(ms: number) {
  const units = [
    { unit: "d", ms: 86_400_000 },
    { unit: "h", ms: 3_600_000 },
    { unit: "min", ms: 60_000 },
    { unit: "s", ms: 1_000 },
  ] as const;
  const { unit, ms: perUnit } = units.find((u) => ms >= u.ms) ?? units[units.length - 1];
  const value = (ms / perUnit).toLocaleString(undefined, { maximumFractionDigits: 1 });
  return { value, unit };
}

/** A period of UTC timestamps, e.g. "14 Jul 2026, 08:00 – 09:00". */
export function formatPeriod(from: string, to: string) {
  const date = { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" } as const;
  const time = { hour: "2-digit", minute: "2-digit", timeZone: "UTC" } as const;
  const start = parseUtc(from);
  const end = parseUtc(to);
  const sameDay =
    start.toLocaleDateString(undefined, date) === end.toLocaleDateString(undefined, date);
  const startText = start.toLocaleString(undefined, { ...date, ...time });
  const endText = sameDay
    ? end.toLocaleTimeString(undefined, time)
    : end.toLocaleString(undefined, { ...date, ...time });
  return `${startText} – ${endText}`;
}

/** A timestamp from the backend, which sends UTC without an offset. */
export function parseUtc(timestamp: string) {
  return new Date(/(?:Z|[+-]\d\d:\d\d)$/i.test(timestamp) ? timestamp : `${timestamp}Z`);
}

/** A flow quantity, e.g. "49.1", "1,990" or "860.1M" for large ones. */
export function formatQuantity(value: number) {
  return Math.abs(value) >= 100_000
    ? value.toLocaleString(undefined, { notation: "compact", maximumFractionDigits: 1 })
    : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/** A count with its noun, e.g. "1 activity", "3 activities". */
export function formatCounted(count: number, singular: string, plural = `${singular}s`) {
  return `${formatCount(count)} ${count === 1 ? singular : plural}`;
}
