import { SaveIcon } from "lucide-react";
import { useRouter } from "next/router";
import { useState } from "react";
import { Button, Flex, Page, Text, TextField } from "../components";
import Classification from "../features/classification/Classification";
import { type Changes, useBuildSocel } from "../hooks/useBuildSocel";
import { useSelectedOcel } from "../hooks/useSelectedOcel";

// Changes the selected sOCEL: the classes of its activities and object types.
// The changed log is kept as a new one, beside the one it came from.
export default function ConfigPage() {
  const router = useRouter();
  const { name: logName } = useSelectedOcel();
  const { build, isBuilding, error } = useBuildSocel();
  const [activities, setActivities] = useState<Changes>({});
  const [objectTypes, setObjectTypes] = useState<Changes>({});
  const [name, setName] = useState<string>();
  const savedName = name ?? (logName ? `${logName} (changed)` : "");
  const changed = Object.keys(activities).length + Object.keys(objectTypes).length > 0;

  const save = () =>
    build({ name: savedName, activities, objectTypes })
      .then(() => router.push("/ocean/overview"))
      .catch(() => undefined);

  return (
    <Page
      title="sOCEL config"
      actions={
        <Flex align="center" gap="2">
          <TextField.Root
            aria-label="Name of the changed log"
            value={savedName}
            onChange={(event) => setName(event.target.value)}
            style={{ width: 260 }}
          />
          <Button
            onClick={save}
            loading={isBuilding}
            disabled={!changed || savedName.trim() === ""}
          >
            <SaveIcon size={16} />
            Save as new log
          </Button>
        </Flex>
      }
    >
      {error && (
        <Text size="2" color="red">
          {error.message}
        </Text>
      )}
      <Classification
        activities={activities}
        objectTypes={objectTypes}
        onActivities={setActivities}
        onObjectTypes={setObjectTypes}
      />
    </Page>
  );
}
