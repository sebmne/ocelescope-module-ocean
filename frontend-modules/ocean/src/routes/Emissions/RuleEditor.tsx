import { Divider, Input, NumberInput, Stack } from "@mantine/core";
import { CardSelector } from "@r4pm/components/ui";
import { ActivityPicker, E2ORelationPicker, RelatedAttributePicker } from "../../components/pickers";
import type { EmissionRule, EmissionRuleType } from "./types";

const ruleTypes = [
  { value: "E" as const, title: "Event", description: "Every event of the activity emits." },
  {
    value: "E2O" as const,
    title: "Event → Object",
    description: "Every relation from an event of the activity to an object emits.",
  },
];

interface RuleEditorProps {
  rule: EmissionRule;
  onChange: (changes: Partial<EmissionRule>) => void;
}

// The form for one rule, shown in the drawer. Changes apply immediately.
export default function RuleEditor({ rule, onChange }: RuleEditorProps) {
  const setFactor = (changes: Partial<EmissionRule["factor"]>) =>
    onChange({ factor: { ...rule.factor, ...changes } });

  // The event attributes, plus object attributes of `objectType` if given.
  const keepAttributes = (objectType: string | undefined) =>
    rule.factor.attributes.filter(
      (ref) => ref.target === "event" || ref.objectType === objectType,
    );

  return (
    <Stack gap="lg">
      <Divider label="Applies to" labelPosition="left" />

      <Input.Wrapper label="Emits per">
        <CardSelector<EmissionRuleType>
          aria-label="Emits per"
          options={ruleTypes}
          value={rule.type}
          // Object attributes chosen for the old type may not fit the new one.
          onValueChange={(type) =>
            onChange({
              type,
              factor: {
                ...rule.factor,
                attributes: keepAttributes(type === "E2O" ? rule.relation?.objectType : undefined),
              },
            })
          }
        />
      </Input.Wrapper>

      <Input.Wrapper label="Activity">
        <ActivityPicker
          variant="dropdown"
          value={rule.activity}
          // A different activity has different relations and attributes: start over.
          onChange={(activity) =>
            onChange({ activity, relation: undefined, factor: { ...rule.factor, attributes: [] } })
          }
        />
      </Input.Wrapper>

      {rule.type === "E2O" && (
        <Input.Wrapper label="Related objects">
          <E2ORelationPicker
            activity={rule.activity}
            value={rule.relation}
            onChange={(relation) =>
              onChange({
                relation,
                factor: { ...rule.factor, attributes: keepAttributes(relation?.objectType) },
              })
            }
          />
        </Input.Wrapper>
      )}

      <Divider label="Emission factor" labelPosition="left" />

      <NumberInput
        label="Value"
        description="Per event, or per unit of the attributes below."
        suffix=" kg CO₂e"
        min={0}
        decimalScale={6}
        value={rule.factor.value ?? ""}
        onChange={(value) => setFactor({ value: typeof value === "number" ? value : undefined })}
      />

      <Input.Wrapper label="Multiply by" description="Numeric attributes only.">
        <RelatedAttributePicker
          activity={rule.activity}
          // E2O: the relation's objects. Event: objects with one value per event.
          objectTypes={rule.type === "E2O" ? (rule.relation ? [rule.relation.objectType] : []) : undefined}
          onlyUniquelyRelated={rule.type === "E"}
          valueTypes={["int", "float"]}
          emptyText="No numeric attributes here."
          value={rule.factor.attributes}
          onChange={(attributes) => setFactor({ attributes })}
        />
      </Input.Wrapper>
    </Stack>
  );
}
