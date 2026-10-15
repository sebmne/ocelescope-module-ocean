import { useGetClassTaxonomies } from "../api/socel";

export type { ClassNode } from "../api/socel";

/** The classes an sOCEL may give its events and its objects; they never change. */
export function useClassTaxonomies() {
  return useGetClassTaxonomies({ query: { staleTime: Number.POSITIVE_INFINITY } });
}
