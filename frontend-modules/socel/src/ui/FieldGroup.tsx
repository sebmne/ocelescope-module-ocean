import { Flex, Separator, Text } from "@r4pm/components/ui";
import type { ReactNode } from "react";

interface FieldGroupProps {
  title: string;
  children: ReactNode;
}

// Fields that belong together in a form, under a small title.
export default function FieldGroup({ title, children }: FieldGroupProps) {
  return (
    <Flex direction="column" gap="4">
      <Flex align="center" gap="3">
        <Text
          size="1"
          weight="medium"
          color="gray"
          style={{ textTransform: "uppercase", letterSpacing: "0.04em" }}
        >
          {title}
        </Text>
        <Separator size="4" style={{ flex: 1 }} />
      </Flex>
      {children}
    </Flex>
  );
}
