import { Box } from "@r4pm/components/ui";
import type { ReactNode } from "react";

interface PanelProps {
  /** accent: draws the eye, e.g. a live preview. neutral: groups quietly. */
  tone?: "accent" | "neutral";
  children: ReactNode;
}

// A tinted area inside a card or sheet, setting its content apart.
export default function Panel({ tone = "neutral", children }: PanelProps) {
  const color = tone === "accent" ? "accent" : "gray";
  return (
    <Box
      p="3"
      style={{
        borderRadius: "var(--radius-3)",
        background: `var(--${color}-a2)`,
        boxShadow: `inset 0 0 0 1px var(--${color}-a4)`,
      }}
    >
      {children}
    </Box>
  );
}
