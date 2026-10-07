import type { ReactNode } from "react";
import {
  attributeLabel,
  describeValue,
  type EmissionRuleDraft,
} from "../../../model/emissionRules";
import { Strong, Text } from "../../../ui";

// A part of the sentence the user chose; greyed out while not chosen yet.
const Part = ({ children, missing }: { children: ReactNode; missing: string }) =>
  children ? <Strong>{children}</Strong> : <Text color="gray">{missing}</Text>;

// A rule in words, e.g. "Each Drive to Terminal event emits 12 kg CO₂e for each related Truck."
export default function RuleSentence({ rule }: { rule: EmissionRuleDraft }) {
  const attributes = rule.factor.attributes.map(attributeLabel);

  return (
    <Text size="2">
      Each <Part missing="…">{rule.activity}</Part> event emits{" "}
      <Part missing="? kg CO₂e">{describeValue(rule)}</Part>
      {attributes.map((name) => (
        <span key={name}>
          {" "}
          × <Strong>{name}</Strong>
        </span>
      ))}
      {rule.type === "E2O" && (
        <>
          {" "}
          for each related <Part missing="object">{rule.relation?.objectType}</Part>
          {rule.relation?.qualifier && <> ({rule.relation.qualifier})</>}
        </>
      )}
      .
    </Text>
  );
}
