import { Box, Flex, Heading } from "@r4pm/components/ui";
import type { ReactNode } from "react";
import SocelTheme from "./SocelTheme";

interface PageProps {
  title: string;
  children: ReactNode;
}

// Every page of the module: the module theme and a title, over the full width as
// Ocelescope's own pages.
export default function Page({ title, children }: PageProps) {
  return (
    <SocelTheme>
      <Box p="4">
        <Flex direction="column" gap="4">
          <Heading size="7" weight="bold" style={{ letterSpacing: "-0.01em" }}>
            {title}
          </Heading>
          {children}
        </Flex>
      </Box>
    </SocelTheme>
  );
}
