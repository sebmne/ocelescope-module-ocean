import { TextField } from "@r4pm/components/ui";

interface NumberFieldProps {
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  /** Shown inside the field, after the number, e.g. "kg CO₂e". */
  unit?: string;
  min?: number;
  placeholder?: string;
  "aria-label"?: string;
}

// A number input with an optional unit. Empty or invalid input is undefined.
export default function NumberField({
  value,
  onChange,
  unit,
  min,
  placeholder,
  ...rest
}: NumberFieldProps) {
  return (
    <TextField.Root
      type="number"
      inputMode="decimal"
      min={min}
      step="any"
      placeholder={placeholder}
      aria-label={rest["aria-label"]}
      value={value ?? ""}
      onChange={(event) => {
        const number = event.currentTarget.valueAsNumber;
        onChange(Number.isNaN(number) ? undefined : number);
      }}
    >
      {unit && (
        <TextField.Slot side="right">
          <span style={{ color: "var(--gray-10)" }}>{unit}</span>
        </TextField.Slot>
      )}
    </TextField.Root>
  );
}
