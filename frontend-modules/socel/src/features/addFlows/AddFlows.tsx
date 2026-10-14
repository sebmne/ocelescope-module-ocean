import { TagsIcon } from "lucide-react";
import { Button, Flex } from "../../components";
import AttributeFlows from "./AttributeFlows";
import ContainmentCard from "./ContainmentCard";
import FileFlows from "./FileFlows";
import FlowSources, { AddFile } from "./FlowSources";
import FlowTable from "./FlowTable";
import type { AddFlowsState } from "./useAddFlows";

// Adding flows to a log: first the choice of a file or event attributes, then
// their cards, the flows they bring, and which objects lie inside which.
export default function AddFlows({ state }: { state: AddFlowsState }) {
  const { records, attributesOn, setAttributesOn, setOpenFile } = state;
  const upload = (file: File) => {
    records.upload(file);
    setOpenFile(true);
  };

  if (!records.file && !attributesOn) {
    return (
      <FlowSources
        isUploading={records.isUploading}
        error={records.error}
        onFile={upload}
        onAttributes={() => setAttributesOn(true)}
      />
    );
  }

  return (
    <Flex direction="column" gap="4">
      {records.file && (
        <FileFlows
          file={records.file}
          name={records.name}
          mapping={records.mapping}
          preview={records.preview}
          isReading={records.isReading}
          error={records.error}
          initiallyOpen={state.openFile}
          onAssign={records.assign}
          onRemove={() => {
            records.remove();
            setOpenFile(false);
          }}
        />
      )}
      {attributesOn && (
        <AttributeFlows
          choices={state.choices}
          onChange={state.setChoices}
          onClose={() => {
            setAttributesOn(false);
            state.setChoices({});
          }}
        />
      )}
      {(!records.file || !attributesOn) && (
        <Flex gap="2">
          {!records.file && <AddFile isUploading={records.isUploading} onFile={upload} />}
          {!attributesOn && (
            <Button variant="soft" color="gray" onClick={() => setAttributesOn(true)}>
              <TagsIcon size={15} />
              Add event attributes
            </Button>
          )}
        </Flex>
      )}
      <FlowTable
        flows={state.flows}
        drafts={state.drafts}
        categories={state.categories}
        onDefine={state.define}
      />
      {state.flowIds.length > 0 && (
        <ContainmentCard
          flows={state.flowIds}
          containments={state.containments}
          onChange={state.setContainments}
        />
      )}
    </Flex>
  );
}
