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
