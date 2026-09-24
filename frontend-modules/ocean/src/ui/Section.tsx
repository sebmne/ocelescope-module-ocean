import { Box, Card, Flex, Heading, Inset, Text } from "@r4pm/components/ui";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import StatusBadge, { type Status } from "./StatusBadge";

interface SectionProps {
  title: string;
  description?: string;
  /** A step of a workflow: shown as its number instead of an icon. */
  step?: number;
  icon?: LucideIcon;
  /** Where the section stands, shown next to the title's actions. */
  status?: Status;
  /** Buttons in the header, on the right. */
  actions?: ReactNode;
  /** A band at the bottom of the card, e.g. for the section's main button. */
  footer?: ReactNode;
  children: ReactNode;
}

// A card on a page: number or icon, title, status and actions on top, content
// below, and an optional footer band.
export default function Section({
  title,
  description,
  step,
  icon: Icon,
  status,
  actions,
  footer,
  children,
}: SectionProps) {
  const done = status?.tone === "done";

  return (
    <Card size="3">
      <Flex direction="column" gap="5">
        <Flex justify="between" align="start" gap="3" wrap="wrap">
          <Flex gap="3" align="start" minWidth="0">
            {(step !== undefined || Icon) && (
              <Flex
                align="center"
                justify="center"
                flexShrink="0"
                aria-hidden
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: step !== undefined ? "50%" : "var(--radius-3)",
                  background: done ? "var(--accent-9)" : "var(--accent-a3)",
                  color: done ? "var(--accent-contrast)" : "var(--accent-11)",
                  fontWeight: 600,
                  fontSize: "var(--font-size-2)",
                  transition: "background 150ms, color 150ms",
                }}
              >
                {step !== undefined ? step : Icon && <Icon size={17} />}
              </Flex>
            )}
            <Box minWidth="0">
              <Heading as="h2" size="4" style={{ lineHeight: "32px" }}>
                {title}
              </Heading>
              {description && (
                <Text as="p" size="2" color="gray">
                  {description}
                </Text>
              )}
            </Box>
          </Flex>
          {(status || actions) && (
            <Flex align="center" gap="3" style={{ minHeight: 32 }}>
              {status && <StatusBadge {...status} />}
              {actions}
            </Flex>
          )}
        </Flex>

        {children}

        {footer && (
          <Inset side="bottom" clip="padding-box">
            <Box
              px="5"
              py="3"
              style={{ borderTop: "1px solid var(--gray-a4)", background: "var(--gray-a2)" }}
            >
              {footer}
            </Box>
          </Inset>
        )}
      </Flex>
    </Card>
  );
}
