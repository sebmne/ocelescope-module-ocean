import { Flex, Switch, Text } from "@r4pm/components/ui";

interface SwitchFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

// An on/off option with a label and an optional explanation.
export default function SwitchField({
  label,
  description,
  checked,
  onChange,
  disabled,
}: SwitchFieldProps) {
  return (
    <Text as="label" size="2" style={{ cursor: disabled ? "default" : "pointer" }}>
      <Flex gap="3" align="start">
        <Switch mt="1" checked={checked} onCheckedChange={onChange} disabled={disabled} />
        <Flex direction="column">
          <Text weight="medium" color={disabled ? "gray" : undefined}>
            {label}
          </Text>
          {description && (
            <Text size="1" color="gray">
              {description}
            </Text>
          )}
        </Flex>
      </Flex>
    </Text>
  );
}
