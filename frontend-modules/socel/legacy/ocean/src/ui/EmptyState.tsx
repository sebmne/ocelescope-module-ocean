import { Flex, Text } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  /** What will show up here, and how to get there. */
  children?: ReactNode;
  /** The button that fills the empty space. */
  action?: ReactNode;
}

// Stands in for content that does not exist yet, and says how to create it.
export default function EmptyState({ icon: Icon, title, children, action }: EmptyStateProps) {
  return (
    <Flex
      direction="column"
      align="center"
      justify="center"
      gap="2"
      py="6"
      px="4"
      style={{
        border: "1px dashed var(--gray-a6)",
        borderRadius: "var(--radius-4)",
        textAlign: "center",
      }}
    >
      <Flex
        align="center"
        justify="center"
        mb="1"
        style={{
          width: 44,
          height: 44,
          borderRadius: "50%",
          background: "var(--accent-a3)",
          color: "var(--accent-11)",
        }}
      >
        <Icon size={20} aria-hidden />
      </Flex>
      <Text size="3" weight="medium">
        {title}
      </Text>
      {children && (
        <Text as="p" size="2" color="gray" style={{ maxWidth: 420 }}>
          {children}
        </Text>
      )}
      {action && <Flex mt="2">{action}</Flex>}
    </Flex>
  );
}
