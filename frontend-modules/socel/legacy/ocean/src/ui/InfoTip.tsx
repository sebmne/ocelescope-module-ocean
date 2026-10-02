import { Tooltip } from "@r4pm/components/ui";
import { InfoIcon } from "lucide-react";

// An explanation on demand: a small icon next to a label, the text on hover.
export default function InfoTip({ content }: { content: string }) {
  return (
    <Tooltip content={content}>
      <InfoIcon
        size={14}
        aria-label={content}
        style={{ color: "var(--gray-9)", cursor: "help", flexShrink: 0 }}
      />
    </Tooltip>
  );
}
