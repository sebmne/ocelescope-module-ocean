import { Box, Button, Flex, Heading, Text } from "@r4pm/components/ui";
import { ArrowLeftIcon } from "lucide-react";
import type { ReactNode } from "react";
import SocelTheme from "./SocelTheme";

interface PageProps {
  title: string;
  /** Shown beside the title in grey, e.g. what the page is about. */
  subtitle?: string;
  /** Where the page came from: a link back, above the title. */
  back?: { label: string; onClick: () => void };
  /** Shown opposite the title, e.g. the page's main action. */
  actions?: ReactNode;
  children: ReactNode;
}

// Every page of the module: the module theme and a title, over the full width as
// Ocelescope's own pages.
export default function Page({ title, subtitle, back, actions, children }: PageProps) {
  return (
    <SocelTheme>
      <Box p="4">
        <Flex direction="column" gap="4">
          <Flex direction="column" gap="2">
            {back && (
              <Box>
                <Button variant="ghost" color="gray" size="1" onClick={back.onClick}>
                  <ArrowLeftIcon size={14} />
                  {back.label}
                </Button>
              </Box>
            )}
            <Flex align="center" justify="between" gap="3" wrap="wrap">
              <Flex align="baseline" gap="3" wrap="wrap">
                <Heading size="7" weight="bold" style={{ letterSpacing: "-0.01em" }}>
                  {title}
                </Heading>
                {subtitle && (
                  <Text size="2" color="gray">
                    {subtitle}
                  </Text>
                )}
              </Flex>
              {actions}
            </Flex>
          </Flex>
          {children}
        </Flex>
      </Box>
    </SocelTheme>
  );
}
