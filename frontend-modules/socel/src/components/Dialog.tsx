import { Group, Modal, NativeSelect, ScrollArea } from "@mantine/core";
import type { ReactNode } from "react";
import SocelTheme from "./SocelTheme";

interface DialogProps {
  opened: boolean;
  onClose: () => void;
  title: string;
  /** What the dialog's buttons are, at its bottom right. */
  footer?: ReactNode;
  children: ReactNode;
}

// A popup as the exploration page opens them: centred on the screen, with a
// title, its content scrolling, and its buttons at the bottom right. Its content
// carries the module's theme, as it is drawn outside the page.
export default function Dialog({ opened, onClose, title, footer, children }: DialogProps) {
  return (
    <Modal opened={opened} onClose={onClose} title={title} size="xl" centered>
      <SocelTheme>
        <ScrollArea.Autosize mah="68vh" type="auto" offsetScrollbars>
          {children}
        </ScrollArea.Autosize>
        {footer && (
          <Group justify="flex-end" gap="sm" mt="md">
            {footer}
          </Group>
        )}
      </SocelTheme>
    </Modal>
  );
}

/** A small choice among a few named options, as the browser draws it: it
 * works inside a scrolling table, where a floating list would be cut off. */
export function SmallChoice({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <NativeSelect
      aria-label={label}
      size="xs"
      value={value}
      data={options.map((option) => ({ value: option.value, label: option.label }))}
      onChange={(event) => onChange(event.currentTarget.value)}
    />
  );
}
