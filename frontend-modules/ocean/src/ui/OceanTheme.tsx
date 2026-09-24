import { Theme } from "@r4pm/components/ui";
import type { ReactNode } from "react";

// OCEAn's design language: one place for colours, radius and scale. Nested in
// the r4pm Theme Ocelescope wraps the app in, so it overrides only these.
export default function OceanTheme({ children }: { children: ReactNode }) {
  return (
    <Theme
      accentColor="teal"
      grayColor="sage"
      radius="medium"
      scaling="100%"
      panelBackground="solid"
      // Let the Ocelescope shell's background show through.
      hasBackground={false}
    >
      {children}
    </Theme>
  );
}
