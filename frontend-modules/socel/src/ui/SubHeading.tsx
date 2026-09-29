import { Flex, Heading } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";

// A heading inside a section, e.g. over one of its columns.
export default function SubHeading({ icon: Icon, title }: { icon: LucideIcon; title: string }) {
  return (
    <Flex align="center" gap="2" mb="3" style={{ color: "var(--gray-11)" }}>
      <Icon size={15} aria-hidden />
      <Heading as="h3" size="2">
        {title}
      </Heading>
    </Flex>
  );
}
