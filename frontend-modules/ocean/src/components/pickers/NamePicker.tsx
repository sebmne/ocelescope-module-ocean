import { Group, Stack, Text } from "@mantine/core";
import { FrequencyPicker, softBadgeStyle, useColorOf } from "@r4pm/components";
import { Badge, Combobox } from "@r4pm/components/ui";
import { XIcon } from "lucide-react";
import { chosen, report, type Selection } from "./types";

/** A name to pick, and how often it occurs. */
export interface NameItem {
  key: string;
  count: number;
}

export interface NamePickerProps {
  /** Name to count, or the same as a list. */
  items: Record<string, number> | readonly NameItem[];
  label?: string;
  /** A search box above the list. */
  searchable?: boolean;
  /** A bar behind each name, as long as its share of the largest count. */
  bars?: boolean;
  /** The count itself, beside each name. */
  counts?: boolean;
  /** The rail that drags a cut through the list, taking the top names. */
  cutoff?: boolean;
  sort?: "count" | "name";
  /** Colour scope, so a name keeps the colour the viewers give it. */
  scope?: string;
  loading?: boolean;
  emptyText?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  /** "list" shows every name at once; "dropdown" is a compact searchable
   * select, for forms. List/count props only apply to "list". */
  variant?: "list" | "dropdown";
}

/**
 * Picking names out of a list, with what is known about how often each occurs.
 *
 * Presentational: it is handed the names and reports back what was picked.
 * `ActivityPicker` and the others wrap it around an endpoint.
 */
export const NamePicker = ({ variant = "list", ...props }: NamePickerProps & Selection) =>
  variant === "dropdown" ? <NameDropdown {...props} /> : <NameList {...props} />;

const NameList = ({
  items,
  label,
  searchable = true,
  bars = true,
  counts = true,
  cutoff = false,
  sort = "count",
  scope = "name",
  loading = false,
  emptyText,
  disabled = false,
  autoFocus,
  ...selection
}: NamePickerProps & Selection) => (
  <Stack gap={4}>
    {label && (
      <Text size="xs" c="dimmed">
        {label}
      </Text>
    )}
    <FrequencyPicker
      items={items as Record<string, number> | NameItem[]}
      mode={selection.multiple ? "multi" : "single"}
      value={chosen(selection)}
      onChange={(next) => !disabled && report(selection, next)}
      searchable={searchable}
      showBars={bars}
      showCounts={counts}
      showCutoff={cutoff}
      sort={sort}
      scope={scope}
      autoFocus={autoFocus}
      emptyText={emptyText ?? (loading ? "Reading the OCEL…" : "Nothing here")}
    />
  </Stack>
);

/** The names, most frequent first (or by name), as the dropdown lists them. */
const sortedNames = (items: NamePickerProps["items"], sort: "count" | "name") => {
  const list = Array.isArray(items)
    ? (items as readonly NameItem[])
    : Object.entries(items).map(([key, count]) => ({ key, count }));
  return [...list]
    .sort((a, b) => (sort === "name" ? a.key.localeCompare(b.key) : b.count - a.count))
    .map((item) => item.key);
};

const NameDropdown = ({
  items,
  label,
  sort = "count",
  scope = "name",
  loading = false,
  emptyText,
  disabled = false,
  autoFocus,
  ...selection
}: NamePickerProps & Selection) => {
  const colorOf = useColorOf(scope);
  const picked = chosen(selection);
  const names = sortedNames(items, sort);

  const placeholder = loading
    ? "Reading the OCEL…"
    : names.length === 0
      ? (emptyText ?? "Nothing here")
      : "Choose…";

  return (
    <Stack gap={4}>
      {label && (
        <Text size="xs" c="dimmed">
          {label}
        </Text>
      )}

      {selection.multiple && picked.size > 0 && (
        <Group gap={6}>
          {[...picked].map((name) => (
            <Badge key={name} style={softBadgeStyle(colorOf(name))}>
              {name}
              {!disabled && (
                <XIcon
                  size={12}
                  role="button"
                  aria-label={`Remove ${name}`}
                  style={{ cursor: "pointer" }}
                  onClick={() => report(selection, [...picked].filter((n) => n !== name))}
                />
              )}
            </Badge>
          ))}
        </Group>
      )}

      <Combobox
        // Multi: the box only adds names, so it stays empty and open for the next.
        value={selection.multiple ? "" : (selection.value ?? undefined)}
        options={selection.multiple ? names.filter((name) => !picked.has(name)) : names}
        onValueChange={(name) =>
          report(selection, selection.multiple ? [...picked, name] : [name])
        }
        keepOpenOnSelect={selection.multiple}
        autoOpen={autoFocus}
        optionColor={colorOf}
        placeholder={selection.multiple ? "Add…" : placeholder}
        emptyLabel={emptyText ?? "Nothing here"}
        disabled={disabled || loading || names.length === 0}
        aria-label={label}
        style={{ width: "100%" }}
      />
    </Stack>
  );
};
