import { Flex, Text } from "@r4pm/components/ui";
import type { ReactNode } from "react";
import InfoTip from "./InfoTip";

interface FieldProps {
  label: string;
  /** An explanation, shown on hovering the label's info icon. */
  info?: string;
  children: ReactNode;
}

// A labelled form field: label, optional info tip, then the input.
export default function Field({ label, info, children }: FieldProps) {
  return (
    <Flex direction="column" gap="1">
      <Flex align="center" gap="1">
        <Text as="div" size="2" weight="medium">
          {label}
        </Text>
        {info && <InfoTip content={info} />}
      </Flex>
      <div>{children}</div>
    </Flex>
  );
}
