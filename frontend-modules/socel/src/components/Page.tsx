import { Box, Flex, Heading } from "@r4pm/components/ui";
import type { ReactNode } from "react";
import SocelTheme from "./SocelTheme";

interface PageProps {
  title: string;
  /** Shown opposite the title, e.g. the page's main action. */
  actions?: ReactNode;
  children: ReactNode;
}

// Every page of the module: the module theme and a title, over the full width as
// Ocelescope's own pages.
export default function Page({ title, actions, children }: PageProps) {
  return (
    <SocelTheme>
      <Box p="4">
        <Flex direction="column" gap="4">
          <Flex align="center" justify="between" gap="3" wrap="wrap">
            <Heading size="7" weight="bold" style={{ letterSpacing: "-0.01em" }}>
              {title}
            </Heading>
            {actions}
          </Flex>
          {children}
        </Flex>
      </Box>
    </SocelTheme>
  );
}
