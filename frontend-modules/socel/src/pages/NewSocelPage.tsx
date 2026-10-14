import { ArrowLeftIcon, ArrowRightIcon, SparklesIcon, TagsIcon } from "lucide-react";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import { Button, Flex, Page, Section, Text, TextField } from "../components";
import Classification from "../features/classification/Classification";
import AttributeFlows from "../features/newSocel/AttributeFlows";
import ContainmentCard from "../features/newSocel/ContainmentCard";
import {
  type ContainmentDraft,
  problemOf,
  typeContainments,
} from "../features/newSocel/containment";
import FileFlows from "../features/newSocel/FileFlows";
import FlowSources, { AddFile } from "../features/newSocel/FlowSources";
import FlowTable from "../features/newSocel/FlowTable";
import {
  type AttributeChoices,
  attributeFlows,
  definitions,
  type FlowDrafts,
  newFlows,
} from "../features/newSocel/flowDrafts";
import { useEventAttributes } from "../features/newSocel/useEventAttributes";
import { canBeRead, useRecordFile } from "../features/newSocel/useRecordFile";
import { useTypeRelations } from "../features/newSocel/useTypeRelations";
import { type Changes, useBuildSocel } from "../hooks/useBuildSocel";
import { useClassTaxonomies } from "../hooks/useClassTaxonomies";
import { useSelectedOcel } from "../hooks/useSelectedOcel";
import { classOptions } from "../lib/classOptions";
import { formatCount } from "../lib/format";

const STEPS = ["Classes", "Flows", "Create"] as const;

// Makes an sOCEL out of the selected log, in three steps: give its activities
// and object types their classes, add flows from a file and from event
// attributes, and create it as a new log.
export default function NewSocelPage() {
  const router = useRouter();
  const { name: logName } = useSelectedOcel();
  const { build, isBuilding, error } = useBuildSocel();
  const taxonomies = useClassTaxonomies();
  const records = useRecordFile();
  const attributes = useEventAttributes();

  const [step, setStep] = useState(0);
  const [activities, setActivities] = useState<Changes>({});
  const [objectTypes, setObjectTypes] = useState<Changes>({});
  const [choices, setChoices] = useState<AttributeChoices>({});
  // Whether attributes are a source of flows, and whether the file's popup
  // opens as its card first shows.
  const [attributesOn, setAttributesOn] = useState(false);
  const [openFile, setOpenFile] = useState(false);
  const [containments, setContainments] = useState<ContainmentDraft[]>([]);
  const { relations } = useTypeRelations();
  const [drafts, setDrafts] = useState<FlowDrafts>({});
  const [name, setName] = useState<string>();
  const builtName = name ?? (logName ? `${logName} (sOCEL)` : "");

  const categories = useMemo(
    () => classOptions(taxonomies.data?.flowCategories ?? []),
    [taxonomies.data],
  );
  const flows = newFlows(records.preview, attributes.data ?? [], choices);
  const defined = definitions(flows, drafts);
  const flowIds = flows.map((flow) => flow.flowId);
  // A containment that is filled in but cannot be used keeps the sOCEL from being created.
  const badContainments = containments.filter((containment) => {
    const problem = problemOf(containment, relations, containments);
    return problem !== null && problem !== "Not filled in";
  }).length;
  // A file whose columns are not all told is not taken along silently.
  const fileUnread = !!records.file && !canBeRead(records.mapping);

  const create = () =>
    build({
      name: builtName,
      activities,
      objectTypes,
      flows: defined ?? {},
      records:
        records.file && records.preview
          ? { uploadId: records.file.uploadId, mapping: records.mapping }
          : null,
      attributeFlows: attributeFlows(choices),
      containment: typeContainments(containments, flowIds),
    })
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

      {step === 1 &&
        (!records.file && !attributesOn ? (
          <FlowSources
            isUploading={records.isUploading}
            error={records.error}
            onFile={(file) => {
              records.upload(file);
              setOpenFile(true);
            }}
            onAttributes={() => setAttributesOn(true)}
          />
        ) : (
          <Flex direction="column" gap="4">
            {records.file && (
              <FileFlows
                file={records.file}
                name={records.name}
                mapping={records.mapping}
                preview={records.preview}
                isReading={records.isReading}
                error={records.error}
                initiallyOpen={openFile}
                onAssign={records.assign}
                onRemove={() => {
                  records.remove();
                  setOpenFile(false);
                }}
              />
            )}
            {attributesOn && (
              <AttributeFlows
                choices={choices}
                onChange={setChoices}
                onClose={() => {
                  setAttributesOn(false);
                  setChoices({});
                }}
              />
            )}
            {(!records.file || !attributesOn) && (
              <Flex gap="2">
                {!records.file && (
                  <AddFile
                    isUploading={records.isUploading}
                    onFile={(file) => {
                      records.upload(file);
                      setOpenFile(true);
                    }}
                  />
                )}
                {!attributesOn && (
                  <Button variant="soft" color="gray" onClick={() => setAttributesOn(true)}>
                    <TagsIcon size={15} />
                    Add event attributes
                  </Button>
                )}
              </Flex>
            )}
            <FlowTable
              flows={flows}
              drafts={drafts}
              categories={categories}
              onDefine={(flowId, draft) =>
                setDrafts((current) => ({ ...current, [flowId]: draft }))
              }
            />
            {flows.length > 0 && (
              <ContainmentCard
                flows={flowIds}
                containments={containments}
                onChange={setContainments}
              />
            )}
          </Flex>
        ))}

      {step === 2 && (
        <Section icon={SparklesIcon} title="Create">
          <Flex direction="column" gap="3" style={{ maxWidth: 560 }}>
            <Text size="2">
              {formatCount(Object.keys(activities).length)} activities and{" "}
              {formatCount(Object.keys(objectTypes).length)} object types get a class here;{" "}
              {formatCount(flows.length)} flows are added.
            </Text>
            {defined === null && (
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
                  builtName.trim() === "" || defined === null || fileUnread || badContainments > 0
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
