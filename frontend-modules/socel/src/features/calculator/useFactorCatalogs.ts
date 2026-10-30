import { keepPreviousData, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  type CatalogFactor,
  type FactorCatalogInfo,
  getListFactorCatalogsQueryKey,
  resolveCatalogFactor,
  useConnectFactorCatalog,
  useDisconnectFactorCatalog,
  useListFactorCatalogs,
  useSearchFactorCatalog,
} from "../../api/socel";
import { useSettled } from "../../hooks/useSettled";

export type FactorCatalog = FactorCatalogInfo;
export type ListedFactor = CatalogFactor;

export const SEARCH_PAGE_SIZE = 10;

/** The external databases of emission factors, and whether each has a key. */
export function useFactorCatalogs() {
  return useListFactorCatalogs();
}

/** Connects a catalog with the user's key, or forgets it. Either changes what
 * can be searched: the catalogs and every search of them are asked again. */
export function useCatalogKey(catalog: string) {
  const queryClient = useQueryClient();
  const [catalogs] = getListFactorCatalogsQueryKey();
  const refresh = () =>
    queryClient.invalidateQueries({
      predicate: ({ queryKey }) =>
        typeof queryKey[0] === "string" && queryKey[0].startsWith(catalogs),
    });
  const connecting = useConnectFactorCatalog<unknown>({ mutation: { onSuccess: refresh } });
  const disconnecting = useDisconnectFactorCatalog<unknown>({ mutation: { onSuccess: refresh } });

  return {
    connect: (key: string) => connecting.mutateAsync({ catalog, data: { key } }),
    disconnect: () => disconnecting.mutateAsync({ catalog }),
    isConnecting: connecting.isPending,
    isDisconnecting: disconnecting.isPending,
    error: connecting.error ?? disconnecting.error,
  };
}

export interface FactorFilter {
  text: string;
  /** Only factors that can be given per this unit; null for any. */
  unit: string | null;
  region: string;
}

/** One page of the catalog's factors matching the filter, asked a moment after
 * the user stops typing; nothing without a key or without text. */
export function useFactorSearch(catalog: FactorCatalog, filter: FactorFilter, page: number) {
  const settled = useSettled(filter, 300);
  const text = settled.text.trim();
  const search = useSearchFactorCatalog(
    catalog.id,
    {
      text,
      unit: settled.unit,
      region: settled.region.trim() || null,
      offset: page * SEARCH_PAGE_SIZE,
      limit: SEARCH_PAGE_SIZE,
    },
    {
      query: {
        enabled: catalog.available && text !== "",
        placeholderData: keepPreviousData,
        // A refusal (no key, unreachable) says why; asking again does not help.
        retry: false,
      },
    },
  );
  return { search, isWaiting: text === "" };
}

/** A listed factor in kg CO2e per one unit of the flow, as the catalog gives it. */
export function useResolveFactor(catalog: string, unit: string) {
  return useMutation({
    mutationFn: (ref: string) => resolveCatalogFactor(catalog, encodeURIComponent(ref), { unit }),
  });
}
