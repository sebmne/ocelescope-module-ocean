import { isAxiosError } from "axios";

/** The backend explains problems in `detail`; anything else gets `fallback`. */
export function errorMessage(error: unknown, fallback: string) {
  if (!error) return undefined;
  if (isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail as string;
  }
  return fallback;
}
