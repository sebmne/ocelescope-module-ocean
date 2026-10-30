import { ChevronLeftIcon, ChevronRightIcon, SearchIcon } from "lucide-react";
import { useState } from "react";
import {
  AsyncBoundary,
  Box,
  Button,
  Checkbox,
  Dialog,
  Flex,
  IconButton,
  SmallChoice,
  Text,
  TextField,
} from "../../components";
import { errorMessage } from "../../lib/errors";
import { formatAmount, formatCount } from "../../lib/format";
import CatalogConnection from "./CatalogConnection";
import {
  type FactorCatalog,
  type ListedFactor,
  SEARCH_PAGE_SIZE,
  useFactorCatalogs,
  useFactorSearch,
  useResolveFactor,
} from "./useFactorCatalogs";

/** The factor field a search is for: a flow, in one direction. */
export interface SearchTarget {
  flowId: string;
  category: string | null;
  unit: string;
  direction: "inflow" | "outflow";
}

// Looks a flow's factor up in an external database: the database is chosen,
// connected with the user's key if it is not yet, and searched; the factor used
// is the one the database gives per one unit of the flow.
export default function FactorSearch({
  target,
  onClose,
  onPick,
}: {
  /** The field searched for; null keeps the dialog closed. */
  target: SearchTarget | null;
  onClose: () => void;
  /** Called with the factor in kg CO2e per one unit of the flow. */
  onPick: (value: number) => void;
}) {
  return (
    <Dialog
      opened={target !== null}
      onClose={onClose}
      title={target ? `A factor for ${target.flowId}` : ""}
      footer={
        <Button variant="soft" color="gray" onClick={onClose}>
          Cancel
        </Button>
      }
    >
      {target && (
        <SearchBody key={`${target.flowId}:${target.direction}`} target={target} onPick={onPick} />
      )}
    </Dialog>
  );
}

function SearchBody({ target, onPick }: { target: SearchTarget; onPick: (value: number) => void }) {
  const catalogs = useFactorCatalogs();
  return (
    <Flex direction="column" gap="4">
      <Text size="2" color="gray">
        In kg CO₂e per {target.unit}{" "}
        {target.direction === "inflow" ? "flowing into" : "flowing out of"} the objects
        {target.category ? ` · ${target.category}` : ""}
      </Text>
      <AsyncBoundary
        status={catalogs}
        isEmpty={(list) => list.length === 0}
        loadingLabel="Reading the databases…"
        errorTitle="The databases could not be read"
        emptyState={{ title: "No databases" }}
        onRetry={() => void catalogs.refetch()}
      >
        {(list) => <CatalogPanel catalogs={list} target={target} onPick={onPick} />}
      </AsyncBoundary>
    </Flex>
  );
}

// The chosen database: its connection, and once connected, its factors. The
// first one that is connected is chosen to start with.
function CatalogPanel({
  catalogs,
  target,
  onPick,
}: {
  catalogs: readonly FactorCatalog[];
  target: SearchTarget;
  onPick: (value: number) => void;
}) {
  const [chosen, setChosen] = useState(
    () => (catalogs.find((catalog) => catalog.available) ?? catalogs[0]).id,
  );
  const catalog = catalogs.find((candidate) => candidate.id === chosen) ?? catalogs[0];

  return (
    <Flex direction="column" gap="4">
      {catalogs.length > 1 && (
        <Flex align="center" gap="2">
          <Text size="2" weight="medium">
            Database
          </Text>
          <SmallChoice
            label="Database"
            value={catalog.id}
            options={catalogs.map((option) => ({ value: option.id, label: option.name }))}
            onChange={setChosen}
          />
        </Flex>
      )}
      <CatalogConnection key={catalog.id} catalog={catalog} />
      {catalog.available && (
        <FactorResults key={catalog.id} catalog={catalog} target={target} onPick={onPick} />
      )}
    </Flex>
  );
}

// A flow's id as words to search for: "cold_rolled_steel" is "cold rolled steel".
const suggestedText = (flowId: string) => flowId.replace(/[_-]+/g, " ").trim();

function FactorResults({
  catalog,
  target,
  onPick,
}: {
  catalog: FactorCatalog;
  target: SearchTarget;
  onPick: (value: number) => void;
}) {
  const [text, setText] = useState(() => suggestedText(target.flowId));
  const [region, setRegion] = useState("");
  const [perUnit, setPerUnit] = useState(true);
  const [page, setPage] = useState(0);
  const filter = { text, unit: perUnit ? target.unit : null, region };

  // A changed search starts at its first page.
  const filterKey = JSON.stringify(filter);
  const [seenKey, setSeenKey] = useState(filterKey);
  if (seenKey !== filterKey) {
    setSeenKey(filterKey);
    setPage(0);
  }

  const { search, isWaiting } = useFactorSearch(catalog, filter, page);
  const resolve = useResolveFactor(catalog.id, target.unit);
  const pick = (ref: string) =>
    resolve.mutate(ref, { onSuccess: (resolved) => onPick(resolved.value) });

  return (
    <Flex direction="column" gap="3">
      <Flex gap="2" wrap="wrap">
        <Box flexGrow="1" style={{ minWidth: 220 }}>
          <TextField.Root
            aria-label={`Search ${catalog.name}`}
            placeholder={`Search ${catalog.name}, e.g. electricity`}
            value={text}
            onChange={(event) => setText(event.target.value)}
          >
            <TextField.Slot>
              <SearchIcon size={14} />
            </TextField.Slot>
          </TextField.Root>
        </Box>
        <TextField.Root
          aria-label="Region"
          placeholder="Region, e.g. DE"
          value={region}
          onChange={(event) => setRegion(event.target.value)}
          style={{ width: 150 }}
        />
      </Flex>
      <Text as="label" size="2">
        <Flex as="span" align="center" gap="2">
          <Checkbox checked={perUnit} onCheckedChange={(checked) => setPerUnit(checked === true)} />
          Only factors that can be given per {target.unit}
        </Flex>
      </Text>

      {isWaiting ? null : search.isError ? (
        <Text size="2" color="red">
          {errorMessage(search.error)}
        </Text>
      ) : (
        <AsyncBoundary
          status={search}
          isEmpty={(data) => data.items.length === 0}
          loadingLabel={`Searching ${catalog.name}…`}
          emptyState={{ title: "No factors found" }}
        >
          {(data) => (
            <Flex direction="column" gap="2">
              <Box
                role="list"
                aria-label={`Factors in ${catalog.name}`}
                style={{
                  border: "1px solid var(--gray-a5)",
                  borderRadius: "var(--radius-4)",
                  overflow: "hidden",
                  opacity: search.isPlaceholderData ? 0.6 : 1,
                  transition: "opacity 100ms",
                }}
              >
                {data.items.map((factor, index) => (
                  <ResultRow
                    key={factor.ref}
                    factor={factor}
                    first={index === 0}
                    isPicking={resolve.isPending && resolve.variables === factor.ref}
                    isBlocked={resolve.isPending}
                    onPick={() => pick(factor.ref)}
                  />
                ))}
              </Box>
              {data.total > SEARCH_PAGE_SIZE && (
                <Pager page={page} total={data.total} onPage={setPage} />
              )}
            </Flex>
          )}
        </AsyncBoundary>
      )}

      {resolve.isError && (
        <Text size="2" color="red">
          {errorMessage(resolve.error)}
        </Text>
      )}
    </Flex>
  );
}

// A factor as the database lists it: what it is, where it comes from, and its
// value where the database tells it in a listing.
function ResultRow({
  factor,
  first,
  isPicking,
  isBlocked,
  onPick,
}: {
  factor: ListedFactor;
  first: boolean;
  isPicking: boolean;
  /** Another factor is being taken. */
  isBlocked: boolean;
  onPick: () => void;
}) {
  const origin = [factor.source, factor.region, factor.year].filter(Boolean).join(" · ");
  return (
    <Flex
      role="listitem"
      align="center"
      justify="between"
      gap="3"
      px="3"
      py="2"
      style={{ borderTop: first ? undefined : "1px solid var(--gray-a4)" }}
    >
      <Flex direction="column" minWidth="0">
        <Text size="2" weight="medium" truncate>
          {factor.name}
        </Text>
        {origin && (
          <Text size="1" color="gray" truncate>
            {origin}
          </Text>
        )}
      </Flex>
      <Flex align="center" gap="3" flexShrink="0">
        {factor.value !== null && factor.value !== undefined ? (
          <Text size="2" wrap="nowrap" style={{ fontVariantNumeric: "tabular-nums" }}>
            {formatAmount(factor.value)} <Text color="gray">kg CO₂e / {factor.unit}</Text>
          </Text>
        ) : (
          <Text size="1" color="gray" wrap="nowrap">
            per {factor.unit}
          </Text>
        )}
        <Button
          size="1"
          variant="soft"
          loading={isPicking}
          disabled={isBlocked && !isPicking}
          onClick={onPick}
        >
          Use
        </Button>
      </Flex>
    </Flex>
  );
}

function Pager({
  page,
  total,
  onPage,
}: {
  page: number;
  total: number;
  onPage: (page: number) => void;
}) {
  return (
    <Flex align="center" justify="between" gap="3">
      <Text size="1" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
        {formatCount(page * SEARCH_PAGE_SIZE + 1)}–
        {formatCount(Math.min(total, (page + 1) * SEARCH_PAGE_SIZE))} of {formatCount(total)}
      </Text>
      <Flex gap="2">
        <IconButton
          size="1"
          variant="soft"
          color="gray"
          aria-label="Previous factors"
          disabled={page === 0}
          onClick={() => onPage(page - 1)}
        >
          <ChevronLeftIcon size={14} />
        </IconButton>
        <IconButton
          size="1"
          variant="soft"
          color="gray"
          aria-label="Next factors"
          disabled={(page + 1) * SEARCH_PAGE_SIZE >= total}
          onClick={() => onPage(page + 1)}
        >
          <ChevronRightIcon size={14} />
        </IconButton>
      </Flex>
    </Flex>
  );
}
