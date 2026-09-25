import { CardSelector, CardSelectorContent } from "@r4pm/components/ui";
import type { ReactNode } from "react";

export interface Choice<T extends string> {
  value: T;
  title: string;
  description?: string;
  icon?: ReactNode;
}

interface ChoiceCardsProps<T extends string> {
  choices: readonly Choice<T>[];
  value: T;
  onChange: (value: T) => void;
  "aria-label": string;
  columns?: 2 | 3 | 4;
  /** Options of the selected choice, shown in a panel below the cards. */
  children?: ReactNode;
}

// Pick one of a few options that need a sentence each to be understood.
export default function ChoiceCards<T extends string>({
  choices,
  value,
  onChange,
  columns,
  children,
  ...rest
}: ChoiceCardsProps<T>) {
  return (
    <CardSelector<T>
      aria-label={rest["aria-label"]}
      options={[...choices]}
      value={value}
      onValueChange={onChange}
      columns={columns}
    >
      {children && <CardSelectorContent>{children}</CardSelectorContent>}
    </CardSelector>
  );
}
