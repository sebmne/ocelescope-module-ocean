import { ObjectTypePicker } from "../../../components/pickers";
import { useAllocateEmissions } from "../../../data/useAllocateEmissions";
import { useEmissionsOverview } from "../../../data/useEmissionsOverview";
import { useObjectEmissions } from "../../../data/useObjectEmissions";
import {
  type AllocationRule,
  allocationBlocker,
  sameAllocationConfig,
} from "../../../model/allocation";
import {
  Button,
  ChoiceCards,
  Field,
  Flex,
  Notice,
  Section,
  type Status,
  SwitchField,
  Text,
} from "../../../ui";
import { allocationRules } from "./allocationRules";
import { useAllocationConfig } from "./useAllocationConfig";

interface AllocationSectionProps {
  /** The section's place in the page's workflow. */
  step: number;
}

// Distributes the computed event emissions to objects of the target types.
export default function AllocationSection({ step }: AllocationSectionProps) {
  const stored = useObjectEmissions();
  const [config, update] = useAllocationConfig(stored.data?.config, stored.isSuccess);
  const allocation = useAllocateEmissions();
  const allocated = stored.data != null;
  const computed = useEmissionsOverview().data?.totalKg != null;
  const blocker = allocationBlocker(config, computed);

  const status: Status = allocation.isPending
    ? { tone: "busy", label: "Allocating" }
    : !allocated
      ? { tone: "idle", label: "Not allocated" }
      : stored.data && !sameAllocationConfig(stored.data.config, config)
        ? { tone: "attention", label: "Settings changed" }
        : { tone: "done", label: "Allocated" };

  return (
    <Section
      step={step}
      title="Allocation"
      status={status}
      footer={
        <Flex justify="end" align="center" gap="3" wrap="wrap">
          {blocker && (
            <Text size="2" color="gray">
              {blocker}
            </Text>
          )}
          <Button
            onClick={() => allocation.allocate(config)}
            disabled={blocker !== undefined}
            loading={allocation.isPending}
            variant={status.tone === "done" ? "soft" : "solid"}
          >
            {allocated ? "Reallocate" : "Allocate"}
          </Button>
        </Flex>
      }
    >
      <Field
        label="Target object types"
        info="The objects that carry the emissions in the end, e.g. orders or products."
      >
        <ObjectTypePicker
          variant="dropdown"
          multiple
          value={config.targetObjectTypes}
          onChange={(targetObjectTypes) => update({ targetObjectTypes })}
        />
      </Field>

      <Field label="Allocation rule">
        <ChoiceCards<AllocationRule>
          aria-label="Allocation rule"
          choices={allocationRules}
          value={config.rule}
          onChange={(rule) => update({ rule })}
        >
          {/* These options only change how the object graph is built, which only
              the "Closest" rule uses. */}
          {config.rule === "ClosestTargets" && (
            <Flex direction="column" gap="4">
              <Field
                label="Resources"
                info="Object types that serve many objects, e.g. trucks or forklifts. Emissions do not pass through them, so they do not spread to everything a truck ever carried."
              >
                <ObjectTypePicker
                  variant="dropdown"
                  multiple
                  value={config.resourceObjectTypes}
                  // Without resources there is nothing to pass via.
                  onChange={(resourceObjectTypes) =>
                    update({
                      resourceObjectTypes,
                      passViaResources:
                        resourceObjectTypes.length > 0 ? config.passViaResources : false,
                    })
                  }
                />
              </Field>
              <SwitchField
                label="Pass emissions via resources"
                info="Treat resources like every other object after all."
                disabled={config.resourceObjectTypes.length === 0}
                checked={config.passViaResources}
                onChange={(passViaResources) => update({ passViaResources })}
              />
              <SwitchField
                label="Pass emissions between objects of the same type"
                checked={config.passBetweenSameType}
                onChange={(passBetweenSameType) => update({ passBetweenSameType })}
              />
            </Flex>
          )}
        </ChoiceCards>
      </Field>

      {allocation.error && <Notice tone="error">{allocation.error}</Notice>}
    </Section>
  );
}
