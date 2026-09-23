import { Button, Group, Input, Stack, Switch, Tooltip } from "@mantine/core";
import { CardSelector } from "@r4pm/components/ui";
import { NetworkIcon } from "lucide-react";
import { useState } from "react";
import { ObjectTypePicker } from "../../components/pickers";
import Section from "./Section";
import type { AllocationConfig, AllocationRule } from "./types";

const allocationRules: { value: AllocationRule; title: string; description: string }[] = [
  {
    value: "ParticipatingTargets",
    title: "Participating",
    description: "An event's emissions are split evenly among the target objects it involves.",
  },
  {
    value: "ClosestTargets",
    title: "Closest",
    description: "An event's emissions go to the nearest target objects in the object graph.",
  },
  {
    value: "AllTargets",
    title: "All",
    description: "All emissions are split evenly among all target objects.",
  },
];

// Distributes the computed event emissions to objects of the target types.
export default function ObjectAllocationSection() {
  const [config, setConfig] = useState<AllocationConfig>({
    targetObjectTypes: [],
    rule: "ParticipatingTargets",
    passViaResources: false,
    passBetweenSameType: true,
  });

  const update = (changes: Partial<AllocationConfig>) =>
    setConfig((config) => ({ ...config, ...changes }));

  return (
    <Section
      icon={NetworkIcon}
      title="Object allocation"
      description="Distribute the event emissions to the objects they belong to."
    >
      <Input.Wrapper label="Target object types">
        <ObjectTypePicker
          variant="dropdown"
          multiple
          value={config.targetObjectTypes}
          onChange={(targetObjectTypes) => update({ targetObjectTypes })}
        />
      </Input.Wrapper>

      <Input.Wrapper label="Allocation rule">
        <CardSelector<AllocationRule>
          aria-label="Allocation rule"
          options={allocationRules}
          value={config.rule}
          onValueChange={(rule) => update({ rule })}
        />
      </Input.Wrapper>

      {/* These options only change how the object graph is built, which only
          the "Closest" rule uses. */}
      {config.rule === "ClosestTargets" && (
        <Stack gap="xs">
          <Switch
            label="Pass emissions via resources"
            checked={config.passViaResources}
            onChange={(event) => update({ passViaResources: event.currentTarget.checked })}
          />
          <Switch
            label="Pass emissions between objects of the same type"
            checked={config.passBetweenSameType}
            onChange={(event) => update({ passBetweenSameType: event.currentTarget.checked })}
          />
        </Stack>
      )}

      <Group justify="flex-end">
        {/* TODO(backend): send `config` and show the object emissions. */}
        <Tooltip label="Needs the OCEAn backend">
          <Button disabled>Allocate</Button>
        </Tooltip>
      </Group>
    </Section>
  );
}
