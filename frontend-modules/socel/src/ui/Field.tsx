import { Flex, Text } from "@r4pm/components/ui";
import type { ReactNode } from "react";

interface FieldProps {
  label: string;
  description?: string;
  children: ReactNode;
}

// A labelled form field: label, optional description, then the input.
export default function Field({ label, description, children }: FieldProps) {
  return (
    <Flex direction="column" gap="1">
      <Text as="div" size="2" weight="medium">
        {label}
      </Text>
      {description && (
        <Text as="div" size="1" color="gray">
          {description}
        </Text>
      )}
      <div>{children}</div>
    </Flex>
  );
}
