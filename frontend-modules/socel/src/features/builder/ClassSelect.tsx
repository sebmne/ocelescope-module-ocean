import { Select } from "../../components";
import type { ClassOption } from "./classOptions";

// Radix has no empty value: this one stands for "no class".
const NONE = "__none__";

interface ClassSelectProps {
  options: readonly ClassOption[];
  value: string | null;
  onChange: (value: string | null) => void;
  label: string;
}

// Picks a class or category out of a taxonomy, shown as the tree it is.
export default function ClassSelect({ options, value, onChange, label }: ClassSelectProps) {
  return (
    <Select.Root
      value={value ?? NONE}
      onValueChange={(next) => onChange(next === NONE ? null : next)}
    >
      <Select.Trigger
        aria-label={label}
        variant={value === null ? "surface" : "soft"}
        color={value === null ? "gray" : undefined}
        style={{ width: 240 }}
      >
        {value ?? <span style={{ color: "var(--gray-9)" }}>–</span>}
      </Select.Trigger>
      <Select.Content position="popper">
        <Select.Item value={NONE}>
          <span style={{ color: "var(--gray-10)" }}>–</span>
        </Select.Item>
        <Select.Separator />
        {options.map((option) => (
          <Select.Item key={option.path} value={option.path}>
            <span
              style={{
                paddingLeft: option.depth * 14,
                fontWeight: option.depth === 0 ? 600 : undefined,
              }}
            >
              {option.label}
            </span>
          </Select.Item>
        ))}
      </Select.Content>
    </Select.Root>
  );
}
