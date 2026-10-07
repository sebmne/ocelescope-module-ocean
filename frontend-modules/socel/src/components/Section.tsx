import { Card, Flex, Heading } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface SectionProps {
  title: string;
  icon?: LucideIcon;
  /** Shown beside the title, e.g. badges. */
  aside?: ReactNode;
  children: ReactNode;
}

// A card on a page: icon and title on top, content below.
export default function Section({ title, icon: Icon, aside, children }: SectionProps) {
  return (
    <Card size="3">
      <Flex direction="column" gap="5">
        <Flex gap="3" align="center" minWidth="0" wrap="wrap">
          {Icon && (
            <Flex
              align="center"
              justify="center"
              flexShrink="0"
              aria-hidden
              style={{
                width: 32,
                height: 32,
                borderRadius: "var(--radius-3)",
                background: "var(--gray-a3)",
                color: "var(--gray-11)",
              }}
            >
              <Icon size={17} />
            </Flex>
          )}
          <Heading as="h2" size="4" style={{ lineHeight: "32px" }}>
            {title}
          </Heading>
          {aside}
        </Flex>

        {children}
      </Flex>
    </Card>
  );
}
