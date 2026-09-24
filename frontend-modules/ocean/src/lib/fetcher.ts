// Required by orval.config.ts: every generated API hook sends its request
// through this function. Ocelescope's client attaches the session header.
import { customFetch as fetch } from "@ocelescope/api-client";
import type { AxiosRequestConfig } from "axios";

export const customFetch = async <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): Promise<T> => fetch<T>(config, options);
