import { Flex, Switch, Text } from "@r4pm/components/ui";
import InfoTip from "./InfoTip";

interface SwitchFieldProps {
  label: string;
  /** An explanation, shown on hovering the label's info icon. */
  info?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

// An on/off option with a label and an optional info tip.
export default function SwitchField({
  label,
  info,
  checked,
  onChange,
  disabled,
}: SwitchFieldProps) {
  return (
    <Flex gap="3" align="center">
      <Text as="label" size="2" style={{ cursor: disabled ? "default" : "pointer" }}>
        <Flex gap="3" align="center">
          <Switch checked={checked} onCheckedChange={onChange} disabled={disabled} />
          <Text weight="medium" color={disabled ? "gray" : undefined}>
            {label}
          </Text>
        </Flex>
      </Text>
      {info && <InfoTip content={info} />}
    </Flex>
  );
}
