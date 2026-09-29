import type { FlowAttribution } from "../../../data/analysis/useAttribution";
import { Button, Flex, Text } from "../../../ui";

interface FlowPickerProps {
  flows: readonly FlowAttribution[];
  value: string | undefined;
  onChange: (flowId: string) => void;
}

// The flow the page analyzes: units differ, so flows are looked at one at a time.
export default function FlowPicker({ flows, value, onChange }: FlowPickerProps) {
  return (
    <Flex gap="2" wrap="wrap" role="radiogroup" aria-label="Flow">
      {flows.map((flow) => {
        const selected = flow.flowId === value;
        return (
          <Button
            key={flow.flowId}
            role="radio"
            aria-checked={selected}
            variant={selected ? "solid" : "soft"}
            color={selected ? undefined : "gray"}
            onClick={() => onChange(flow.flowId)}
          >
            {flow.flowId}
            <Text size="1" style={{ opacity: 0.7 }}>
              {flow.unit}
            </Text>
          </Button>
        );
      })}
    </Flex>
  );
}
