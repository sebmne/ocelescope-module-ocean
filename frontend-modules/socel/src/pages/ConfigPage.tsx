import { SaveIcon } from "lucide-react";
import { useState } from "react";
import { Button, Page, Text } from "../components";
import Classification from "../features/classification/Classification";
import FlowConfig from "../features/flowConfig/FlowConfig";
import { useFlowEdits } from "../features/flowConfig/useFlowEdits";
import type { Changes } from "../hooks/useBuildSocel";
import { useConfigureSocel } from "../hooks/useConfigureSocel";

// Changes the selected sOCEL in place: the classes of its activities and object
// types, and its flows. The log keeps its id and name, so it is exported as
// changed.
export default function ConfigPage() {
  const { configure, isSaving, error } = useConfigureSocel();
  const flows = useFlowEdits();
  const [activities, setActivities] = useState<Changes>({});
  const [objectTypes, setObjectTypes] = useState<Changes>({});
  const changed =
    Object.keys(activities).length + Object.keys(objectTypes).length + flows.edits.length > 0;

  const save = () =>
    configure({ activities, objectTypes, flowEdits: flows.edits })
      .then(() => {
        setActivities({});
        setObjectTypes({});
        flows.reset();
      })
      .catch(() => undefined);

  return (
    <Page
      title="sOCEL config"
      actions={
        <Button onClick={save} loading={isSaving} disabled={!changed || flows.hasProblems}>
          <SaveIcon size={16} />
          Save
        </Button>
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
      <FlowConfig state={flows} />
    </Page>
  );
}
