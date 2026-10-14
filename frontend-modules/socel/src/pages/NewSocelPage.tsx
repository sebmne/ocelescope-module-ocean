import { ArrowLeftIcon, ArrowRightIcon, SparklesIcon } from "lucide-react";
import { useRouter } from "next/router";
import { useState } from "react";
import { Button, Flex, Page, Section, Text, TextField } from "../components";
import AddFlows from "../features/addFlows/AddFlows";
import { useAddFlows } from "../features/addFlows/useAddFlows";
import Classification from "../features/classification/Classification";
import { type Changes, useBuildSocel } from "../hooks/useBuildSocel";
import { useSelectedOcel } from "../hooks/useSelectedOcel";
import { formatCount } from "../lib/format";

const STEPS = ["Classes", "Flows", "Create"] as const;

// Makes an sOCEL out of the selected log, in three steps: give its activities
// and object types their classes, add flows from a file and from event
// attributes, and create it as a new log.
export default function NewSocelPage() {
  const router = useRouter();
  const { name: logName } = useSelectedOcel();
  const { build, isBuilding, error } = useBuildSocel();
  const added = useAddFlows();

  const [step, setStep] = useState(0);
  const [activities, setActivities] = useState<Changes>({});
  const [objectTypes, setObjectTypes] = useState<Changes>({});
  const [name, setName] = useState<string>();
  const builtName = name ?? (logName ? `${logName} (sOCEL)` : "");
  const { undefinedFlows, badContainments, fileUnread } = added.problems;

  const create = () =>
    build({ name: builtName, activities, objectTypes, ...added.changes })
      .then(() => router.push("/ocean/overview"))
      .catch(() => undefined);

  return (
    <Page
      title="New sOCEL"
      actions={
        <Flex align="center" gap="2">
          {STEPS.map((label, index) => (
            <Button
              key={label}
              variant={index === step ? "solid" : "soft"}
              color={index === step ? undefined : "gray"}
              onClick={() => setStep(index)}
            >
              {index + 1} · {label}
            </Button>
          ))}
        </Flex>
      }
    >
      {step === 0 && (
        <Classification
          activities={activities}
          objectTypes={objectTypes}
          onActivities={setActivities}
          onObjectTypes={setObjectTypes}
        />
      )}

      {step === 1 && <AddFlows state={added} />}

      {step === 2 && (
        <Section icon={SparklesIcon} title="Create">
          <Flex direction="column" gap="3" style={{ maxWidth: 560 }}>
            <Text size="2">
              {formatCount(Object.keys(activities).length)} activities and{" "}
              {formatCount(Object.keys(objectTypes).length)} object types get a class here;{" "}
              {formatCount(added.flows.length)} flows are added.
            </Text>
            {undefinedFlows && (
              <Text size="2" color="amber">
                Every flow needs a unit and a category: see step 2.
              </Text>
            )}
            {badContainments > 0 && (
              <Text size="2" color="amber">
                A containment cannot be used: see step 2.
              </Text>
            )}
            {fileUnread && (
              <Text size="2" color="amber">
                The file's columns are not all assigned: see step 2, or leave the file out.
              </Text>
            )}
            {error && (
              <Text size="2" color="red">
                {error.message}
              </Text>
            )}
            <Flex align="center" gap="2">
              <TextField.Root
                aria-label="Name of the new log"
                value={builtName}
                onChange={(event) => setName(event.target.value)}
                style={{ flex: 1 }}
              />
              <Button
                onClick={create}
                loading={isBuilding}
                disabled={
                  builtName.trim() === "" || undefinedFlows || fileUnread || badContainments > 0
                }
              >
                <SparklesIcon size={16} />
                Create sOCEL
              </Button>
            </Flex>
          </Flex>
        </Section>
      )}

      <Flex justify="between">
        <Button variant="soft" color="gray" disabled={step === 0} onClick={() => setStep(step - 1)}>
          <ArrowLeftIcon size={16} />
          Back
        </Button>
        {step < STEPS.length - 1 && (
          <Button variant="soft" onClick={() => setStep(step + 1)}>
            Next
            <ArrowRightIcon size={16} />
          </Button>
        )}
      </Flex>
    </Page>
  );
}
