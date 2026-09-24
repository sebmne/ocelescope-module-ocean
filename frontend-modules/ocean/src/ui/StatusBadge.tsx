import { Badge, Spinner } from "@r4pm/components/ui";
import { CircleCheckIcon, CircleDashedIcon, RefreshCwIcon } from "lucide-react";

/** done: finished and current. attention: needs to be redone. idle: not done yet. busy: running. */
export type StatusTone = "done" | "attention" | "idle" | "busy";

export interface Status {
  tone: StatusTone;
  label: string;
}

const looks = {
  done: { color: "teal", icon: <CircleCheckIcon size={12} aria-hidden /> },
  attention: { color: "amber", icon: <RefreshCwIcon size={12} aria-hidden /> },
  idle: { color: "gray", icon: <CircleDashedIcon size={12} aria-hidden /> },
  busy: { color: "gray", icon: <Spinner size="1" /> },
} as const;

// Where something stands, in a word or two.
export default function StatusBadge({ tone, label }: Status) {
  const { color, icon } = looks[tone];
  return (
    <Badge color={color} variant="soft" radius="full" size="2">
      {icon}
      {label}
    </Badge>
  );
}
