import { Box, Button, Flex, Popover, Spinner, Text, TextField } from "@r4pm/components/ui";
import { CheckIcon, ChevronsUpDownIcon, SearchIcon } from "lucide-react";
import { type KeyboardEvent, useId, useState } from "react";
import type { SinglePicker } from "./types";

export interface IdPickerProps {
  /** The ids to offer. Usually a page of them, from a search. */
  ids: readonly string[];
  label?: string;
  placeholder?: string;
  /** What the reader has typed, when the caller searches for them. */
  search?: string;
  onSearch?: (search: string) => void;
  loading?: boolean;
  emptyText?: string;
  disabled?: boolean;
}

/**
 * Picking an id by typing.
 *
 * Presentational: a log holds far more events and objects than a list can
 * show, so the caller decides which ids a search turns up. Unlike core's, built
 * on a Radix popover, so it also works inside Radix dialogs - a Mantine
 * dropdown is portalled outside them, where a modal dialog ignores the mouse.
 * Single selection only, for now.
 */
export const IdPicker = ({
  ids,
  label,
  placeholder = "Search…",
  search = "",
  onSearch,
  loading = false,
  emptyText,
  disabled,
  value,
  onChange,
}: IdPickerProps & SinglePicker) => {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const listId = useId();

  const choose = (id: string | undefined) => {
    onChange(id);
    setOpen(false);
    onSearch?.("");
  };

  const navigate = (event: KeyboardEvent) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      setActive((index) => Math.min(Math.max(index + step, 0), Math.max(ids.length - 1, 0)));
    } else if (event.key === "Enter" && ids[active] !== undefined) {
      event.preventDefault();
      choose(ids[active]);
    }
  };

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger disabled={disabled}>
        <Button
          variant="surface"
          color="gray"
          aria-label={label ?? placeholder}
          style={{ width: "100%", justifyContent: "space-between", fontWeight: "normal" }}
        >
          <Text truncate color={value ? undefined : "gray"}>
            {value ?? placeholder}
          </Text>
          <ChevronsUpDownIcon size={14} aria-hidden />
        </Button>
      </Popover.Trigger>
      <Popover.Content
        size="1"
        align="start"
        style={{ width: "var(--radix-popover-trigger-width)", minWidth: 240, padding: 6 }}
      >
        <TextField.Root
          autoFocus
          size="2"
          value={search}
          placeholder="Search by id"
          role="combobox"
          aria-expanded
          aria-controls={listId}
          aria-activedescendant={ids[active] !== undefined ? `${listId}-${active}` : undefined}
          onChange={(event) => {
            onSearch?.(event.currentTarget.value);
            setActive(0);
          }}
          onKeyDown={navigate}
        >
          <TextField.Slot>
            <SearchIcon size={14} aria-hidden />
          </TextField.Slot>
          {loading && (
            <TextField.Slot side="right">
              <Spinner size="1" />
            </TextField.Slot>
          )}
        </TextField.Root>

        <Box id={listId} role="listbox" mt="1" style={{ maxHeight: 240, overflowY: "auto" }}>
          {ids.length === 0 ? (
            <Box p="2">
              <Text size="1" color="gray">
                {emptyText ?? (loading ? "Searching…" : "Nothing found")}
              </Text>
            </Box>
          ) : (
            ids.map((id, index) => (
              <Flex
                key={id}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={id === value}
                align="center"
                justify="between"
                gap="2"
                px="2"
                py="1"
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(id)}
                style={{
                  cursor: "pointer",
                  borderRadius: "var(--radius-2)",
                  background: index === active ? "var(--accent-a3)" : undefined,
                }}
              >
                <Text size="2" truncate>
                  {id}
                </Text>
                {id === value && <CheckIcon size={14} aria-hidden />}
              </Flex>
            ))
          )}
        </Box>

        {value && (
          <Button variant="ghost" color="gray" size="1" mt="1" onClick={() => choose(undefined)}>
            Clear
          </Button>
        )}
      </Popover.Content>
    </Popover.Root>
  );
};
