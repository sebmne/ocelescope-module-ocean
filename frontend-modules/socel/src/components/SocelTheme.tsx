import { Theme } from "@r4pm/components/ui";
import type { ReactNode } from "react";

// The module's design language, nested in the r4pm Theme Ocelescope wraps the app
// in. Surfaces, icons and badges are neutral; the one accent is Ocelescope's blue,
// kept for actions and for the marks that carry the data.
export default function SocelTheme({ children }: { children: ReactNode }) {
  return (
    <Theme
      accentColor="blue"
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
