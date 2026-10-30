import { isAxiosError } from "axios";

/** What went wrong, in the backend's words where it gave them (its `detail`),
 * else the error's own message. */
export function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return error instanceof Error ? error.message : String(error);
}
