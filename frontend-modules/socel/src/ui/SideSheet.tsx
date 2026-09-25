import { Box, Dialog, Flex, IconButton, Text } from "@r4pm/components/ui";
import { XIcon } from "lucide-react";
import type { ReactNode } from "react";

interface SideSheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  /** Buttons pinned to the bottom of the sheet. */
  footer?: ReactNode;
  children: ReactNode;
}

// A panel sliding over the right edge, for editing without leaving the page.
// (Radix has no drawer; this is its Dialog, placed at the side.)
export default function SideSheet({
  open,
  onClose,
  title,
  description,
  footer,
  children,
}: SideSheetProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && onClose()}>
      <Dialog.Content
        aria-describedby={undefined}
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          height: "100vh",
          maxHeight: "100vh",
          width: "min(480px, 100vw)",
          maxWidth: "100vw",
          margin: 0,
          padding: 0,
          borderRadius: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Flex
          justify="between"
          align="start"
          gap="3"
          px="5"
          py="4"
          style={{ borderBottom: "1px solid var(--gray-a4)" }}
        >
          <Box>
            <Dialog.Title size="4" mb="0">
              {title}
            </Dialog.Title>
            {description && (
              <Text as="p" size="2" color="gray">
                {description}
              </Text>
            )}
          </Box>
          <Dialog.Close>
            <IconButton variant="ghost" color="gray" aria-label="Close">
              <XIcon size={18} />
            </IconButton>
          </Dialog.Close>
        </Flex>

        <Box px="5" py="5" style={{ flex: 1, overflowY: "auto" }}>
          {children}
        </Box>

        {footer && (
          <Box
            px="5"
            py="3"
            style={{ borderTop: "1px solid var(--gray-a4)", background: "var(--gray-a2)" }}
          >
            {footer}
          </Box>
        )}
      </Dialog.Content>
    </Dialog.Root>
  );
}
