import { Group, Paper, Stack, Text, ThemeIcon, Title } from "@mantine/core";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface SectionProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  /** Buttons in the header, on the right. */
  actions?: ReactNode;
  children: ReactNode;
}

// The card every section of this page sits in: icon, title and actions on
// top, content below.
export default function Section({ icon: Icon, title, description, actions, children }: SectionProps) {
  return (
    <Paper withBorder radius="md" p="lg">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Group gap="sm" align="flex-start" wrap="nowrap">
            <ThemeIcon variant="light" size="lg" radius="md">
              <Icon size={18} aria-hidden />
            </ThemeIcon>
            <div>
              <Title order={4}>{title}</Title>
              {description && (
                <Text size="sm" c="dimmed">
                  {description}
                </Text>
              )}
            </div>
          </Group>
          {actions}
        </Group>
        {children}
      </Stack>
    </Paper>
  );
}
