import { BoxIcon, CogIcon, SparklesIcon } from "lucide-react";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import { AsyncBoundary, Button, Flex, Grid, Page, Text, TextField } from "../../components";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";
import { classOptions } from "./classOptions";
import FlowsCard from "./FlowsCard";
import TypeCard from "./TypeCard";
import { type Changes, useBuildSocel } from "./useBuildSocel";
import { useClassTaxonomies } from "./useClassTaxonomies";
import { type TypeClassification, useLogClassification } from "./useLogClassification";
import { definedFlows, useRecordFile } from "./useRecordFile";

const classOfIn =
  (types: readonly TypeClassification[], changes: Changes) =>
  (name: string): string | null =>
    name in changes
      ? changes[name]
      : (types.find((type) => type.name === name)?.socelClass ?? null);

// Turns the selected log into an sOCEL: every activity and object type gets a
// class of the taxonomy, flow records come from a file, and the result is added
// as a new log.
export default function SocelBuilder() {
  const router = useRouter();
  const { name: logName } = useSelectedOcel();
  const classification = useLogClassification();
  const taxonomies = useClassTaxonomies();
  const { build, isBuilding, error } = useBuildSocel();
  const records = useRecordFile();

  const [activities, setActivities] = useState<Changes>({});
  const [objectTypes, setObjectTypes] = useState<Changes>({});
  const [name, setName] = useState<string>();
  const builtName = name ?? (logName ? `${logName} (sOCEL)` : "");

  const eventClasses = useMemo(
    () => classOptions(taxonomies.data?.eventClasses ?? []),
    [taxonomies.data],
  );
  const objectClasses = useMemo(
    () => classOptions(taxonomies.data?.objectClasses ?? []),
    [taxonomies.data],
  );

  const flowCategories = useMemo(
    () => classOptions(taxonomies.data?.flowCategories ?? []),
    [taxonomies.data],
  );

  // With a file, every flow that brings records needs its unit and category.
  const flows = records.file ? definedFlows(records.file, records.flows) : {};
  const create = () =>
    build(
      builtName,
      activities,
      objectTypes,
      records.file && flows ? { uploadId: records.file.uploadId, flows } : null,
    )
      .then(() => router.push("/socel/overview"))
      .catch(() => undefined);

  return (
    <Page
      title="Build sOCEL"
      actions={
        <Flex align="center" gap="2">
          <TextField.Root
            aria-label="Name of the new log"
            value={builtName}
            onChange={(event) => setName(event.target.value)}
            style={{ width: 260 }}
          />
          <Button
            onClick={create}
            loading={isBuilding}
            disabled={builtName.trim() === "" || flows === null}
          >
            <SparklesIcon size={16} />
            Create
          </Button>
        </Flex>
      }
    >
      {error && (
        <Text size="2" color="red">
          {error.message}
        </Text>
      )}
      <AsyncBoundary
        status={classification}
        loadingLabel="Reading the log…"
        errorTitle="The log could not be read"
        onRetry={() => void classification.refetch()}
      >
        {(data) => (
          <Flex direction="column" gap="4">
            <Grid columns={{ initial: "1", lg: "2" }} gap="4" align="start">
              <TypeCard
                icon={CogIcon}
                title="Activities"
                colorScope="activity"
                types={data.activities}
                options={eventClasses}
                classOf={classOfIn(data.activities, activities)}
                onChange={(type, socelClass) =>
                  setActivities((current) => ({ ...current, [type]: socelClass }))
                }
              />
              <TypeCard
                icon={BoxIcon}
                title="Object types"
                colorScope="objectType"
                types={data.objectTypes}
                options={objectClasses}
                classOf={classOfIn(data.objectTypes, objectTypes)}
                onChange={(type, socelClass) =>
                  setObjectTypes((current) => ({ ...current, [type]: socelClass }))
                }
              />
            </Grid>
            <FlowsCard
              file={records.file}
              flows={records.flows}
              categories={flowCategories}
              isUploading={records.isUploading}
              error={records.error}
              onUpload={records.upload}
              onDefine={records.define}
            />
          </Flex>
        )}
      </AsyncBoundary>
    </Page>
  );
}
