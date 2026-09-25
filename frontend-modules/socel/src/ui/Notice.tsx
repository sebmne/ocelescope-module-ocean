import { Callout } from "@r4pm/components/ui";
import { CircleAlertIcon, InfoIcon } from "lucide-react";
import type { ReactNode } from "react";

interface NoticeProps {
  tone?: "info" | "error";
  children: ReactNode;
}

// A short message in the flow of the page: an error, or a hint.
export default function Notice({ tone = "info", children }: NoticeProps) {
  const Icon = tone === "error" ? CircleAlertIcon : InfoIcon;
  return (
    <Callout.Root color={tone === "error" ? "red" : undefined} variant="soft" size="1">
      <Callout.Icon>
        <Icon size={16} />
      </Callout.Icon>
      <Callout.Text>{children}</Callout.Text>
    </Callout.Root>
  );
}
