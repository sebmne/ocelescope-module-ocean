import {
  ActivityPicker,
  E2ORelationPicker,
  RelatedAttributePicker,
} from "../../../components/pickers";
import {
  attributesFor,
  describeUnit,
  type EmissionRuleDraft,
  type EmissionRuleType,
} from "../../../model/emissionRules";
import { ChoiceCards, Field, FieldGroup, Flex, NumberField, Panel } from "../../../ui";
import RuleSentence from "./RuleSentence";
import { ruleTypes } from "./ruleTypes";

interface RuleEditorProps {
  rule: EmissionRuleDraft;
  onChange: (changes: Partial<EmissionRuleDraft>) => void;
}

// The form for one rule, shown in the side sheet. Changes apply immediately.
export default function RuleEditor({ rule, onChange }: RuleEditorProps) {
  const setFactor = (changes: Partial<EmissionRuleDraft["factor"]>) =>
    onChange({ factor: { ...rule.factor, ...changes } });

  return (
    <Flex direction="column" gap="6">
      {/* The rule as it reads, updated while editing. */}
      <Panel tone="accent">
        <RuleSentence rule={rule} />
      </Panel>

      <FieldGroup title="Applies to">
        <Field label="Activity">
          <ActivityPicker
            variant="dropdown"
            value={rule.activity}
            // A different activity has different relations and attributes: start over.
            onChange={(activity) =>
              onChange({
                activity,
                relation: undefined,
                factor: { ...rule.factor, attributes: [] },
              })
            }
          />
        </Field>

        <Field label="Applied">
          <ChoiceCards<EmissionRuleType>
            aria-label="Applied"
            choices={ruleTypes}
            value={rule.type}
            // Object attributes chosen for the old type may not fit the new one.
            onChange={(type) =>
              onChange({
                type,
                factor: {
                  ...rule.factor,
                  attributes: attributesFor(
                    rule,
                    type === "E2O" ? rule.relation?.objectType : undefined,
                  ),
                },
              })
            }
          />
        </Field>

        {rule.type === "E2O" && (
          <Field label="Related objects">
            <E2ORelationPicker
              activity={rule.activity}
              value={rule.relation}
              onChange={(relation) =>
                onChange({
                  relation,
                  factor: { ...rule.factor, attributes: attributesFor(rule, relation?.objectType) },
                })
              }
            />
          </Field>
        )}
      </FieldGroup>

      <FieldGroup title="Emission factor">
        <Field
          label="Value"
          description={`Emitted ${describeUnit(rule)}; multiplied by the attributes below, if any.`}
        >
          <NumberField
            aria-label="Value"
            unit="kg CO₂e"
            min={0}
            value={rule.factor.value}
            onChange={(value) => setFactor({ value })}
          />
        </Field>

        <Field label="Multiply by" description="Numeric attributes only.">
          <RelatedAttributePicker
            activity={rule.activity}
            // E2O: the relation's objects. Event: objects with one value per event.
            objectTypes={
              rule.type === "E2O" ? (rule.relation ? [rule.relation.objectType] : []) : undefined
            }
            onlyUniquelyRelated={rule.type === "E"}
            valueTypes={["int", "float"]}
            emptyText="No numeric attributes here."
            value={rule.factor.attributes}
            onChange={(attributes) => setFactor({ attributes })}
          />
        </Field>
      </FieldGroup>
    </Flex>
  );
}
