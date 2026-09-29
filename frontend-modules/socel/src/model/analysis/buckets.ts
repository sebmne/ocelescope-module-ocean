/** The window lengths a flow can be shown in, shortest first. */
export const BUCKETS = ["15min", "hour", "day", "week"] as const;
export type BucketName = (typeof BUCKETS)[number];

export const BUCKET_LABELS: Record<BucketName, string> = {
  "15min": "15 min",
  hour: "Hour",
  day: "Day",
  week: "Week",
};

const HOUR = 3_600_000;

/** The window length that gives a period a readable number of bars (about 4 to 100). */
export function defaultBucket(periodMs: number | undefined): BucketName {
  if (periodMs === undefined || periodMs <= 24 * HOUR) return "15min";
  if (periodMs <= 4 * 24 * HOUR) return "hour";
  if (periodMs <= 100 * 24 * HOUR) return "day";
  return "week";
}
