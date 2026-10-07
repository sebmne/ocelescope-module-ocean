import { Box, Flex, Heading } from "@r4pm/components/ui";
import type { ReactNode } from "react";
import OceanTheme from "./OceanTheme";

interface PageProps {
  title: string;
  children: ReactNode;
}

// Every page of the module: the module theme, a title, and a readable width.
export default function Page({ title, children }: PageProps) {
  return (
    <OceanTheme>
      <Box px={{ initial: "4", md: "6" }} py="6" mx="auto" style={{ maxWidth: 1200 }}>
        <Flex direction="column" gap="5">
          <Heading size="7" weight="bold" style={{ letterSpacing: "-0.01em" }}>
            {title}
          </Heading>
          {children}
        </Flex>
      </Box>
    </OceanTheme>
  );
}
