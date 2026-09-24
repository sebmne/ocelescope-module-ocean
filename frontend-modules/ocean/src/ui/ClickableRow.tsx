import { Flex, Table } from "@r4pm/components/ui";
import { type ReactNode, useState } from "react";

interface ClickableRowProps {
  /** What happens when the row is clicked, or Enter is pressed on it. */
  onClick: () => void;
  /** Accessible name of the row's action, e.g. "Edit rule Load Truck". */
  label: string;
  /** The row's cells (Table.Cell), before the actions. */
  children: ReactNode;
  /** Buttons in the last cell; clicking them does not click the row. */
  actions?: ReactNode;
}

// A table row that opens something, with its own buttons at the end.
export default function ClickableRow({ onClick, label, children, actions }: ClickableRowProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <Table.Row
      tabIndex={0}
      aria-label={label}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          onClick();
        }
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      align="center"
      style={{
        cursor: "pointer",
        background: hovered ? "var(--accent-a2)" : undefined,
        transition: "background 100ms",
      }}
    >
      {children}
      <Table.Cell
        justify="end"
        onClick={(event) => event.stopPropagation()}
        style={{ cursor: "default" }}
      >
        <Flex justify="end" align="center" gap="2">
          {actions}
        </Flex>
      </Table.Cell>
    </Table.Row>
  );
}
