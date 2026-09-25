import { Box, Flex, Heading, Text } from "@r4pm/components/ui";
import type { ReactNode } from "react";
import SocelTheme from "./SocelTheme";

interface PageProps {
  title: string;
  description?: string;
  children: ReactNode;
}

// Every page of the module: the module theme, a header, and a readable width.
export default function Page({ title, description, children }: PageProps) {
  return (
    <SocelTheme>
      <Box px={{ initial: "4", md: "6" }} py="6" mx="auto" style={{ maxWidth: 1200 }}>
        <Flex direction="column" gap="5">
          <Box>
            <Heading size="7" weight="bold" style={{ letterSpacing: "-0.01em" }}>
              {title}
            </Heading>
            {description && (
              <Text as="p" size="3" color="gray" mt="1">
                {description}
              </Text>
            )}
          </Box>
          {children}
        </Flex>
      </Box>
    </SocelTheme>
  );
}
