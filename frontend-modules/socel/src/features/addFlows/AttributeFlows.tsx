import { TagsIcon, XIcon } from "lucide-react";
import {
  AsyncBoundary,
  Checkbox,
  Flex,
  Grid,
  IconButton,
  Section,
  Select,
  Text,
  TextField,
} from "../../components";
import { formatCount } from "../../lib/format";
import type { AttributeChoice, AttributeChoices } from "./flowDrafts";
import { type EventAttribute, useEventAttributes } from "./useEventAttributes";

interface AttributeFlowsProps {
  choices: AttributeChoices;
  onChange: (choices: AttributeChoices) => void;
  /** Leaves attributes out of the flows. */
  onClose: () => void;
}

// Flows from the attributes of the log's events. A chosen attribute becomes a
// flow: each of its values is a record at its event, observed at the event's
// objects of one type. An attribute holds amounts; the direction says whether
// they flow into that object or out of it, which the sOCEL stores as the sign.
export default function AttributeFlows({ choices, onChange, onClose }: AttributeFlowsProps) {
  const attributes = useEventAttributes();
  const set = (attribute: EventAttribute, choice: AttributeChoice | null) => {
    const { [attribute.name]: _, ...others } = choices;
    onChange(choice ? { ...others, [attribute.name]: choice } : others);
  };

  return (
    <Section
      icon={TagsIcon}
      title="From event attributes"
      aside={
        <Flex align="center" gap="2" flexGrow="1" justify="end">
          <Text size="2" color="gray">
            {formatCount(Object.keys(choices).length)} chosen
          </Text>
          <IconButton
            variant="ghost"
            color="gray"
            size="1"
            aria-label="Leave attributes out"
            onClick={onClose}
          >
            <XIcon size={14} />
          </IconButton>
        </Flex>
      }
    >
      <AsyncBoundary
        status={attributes}
        isEmpty={(data) => data.length === 0}
        loadingLabel="Reading the attributes…"
        errorTitle="The attributes could not be read"
        emptyState={{
          title: "No numeric attributes",
          description: "The events of this log have no numeric attribute.",
        }}
        onRetry={() => void attributes.refetch()}
      >
        {(data) => (
          <Grid columns="32px minmax(0, 1.4fr) minmax(0, 1fr) 200px 180px" gap="2" align="center">
            <Label>Use</Label>
            <Label>Attribute</Label>
            <Label>Flow</Label>
            <Label>Measured at</Label>
            <Label>Direction</Label>
            {data.map((attribute) => (
              <Row
                key={attribute.name}
                attribute={attribute}
                choice={choices[attribute.name]}
                onChange={(choice) => set(attribute, choice)}
              />
            ))}
          </Grid>
        )}
      </AsyncBoundary>
    </Section>
  );
}

function Label({ children }: { children: string }) {
  return (
    <Text size="1" color="gray" weight="medium">
      {children}
    </Text>
  );
}

function Row({
  attribute,
  choice,
  onChange,
}: {
  attribute: EventAttribute;
  choice: AttributeChoice | undefined;
  onChange: (choice: AttributeChoice | null) => void;
}) {
  // An attribute no event of which involves an object cannot be placed.
  const placeable = attribute.objectTypes.length > 0;
  return (
    <>
      <Checkbox
        aria-label={`Take ${attribute.name} as a flow`}
        checked={!!choice}
        disabled={!placeable}
        onCheckedChange={(checked) =>
          onChange(
            checked === true
              ? {
                  flowId: attribute.name,
                  objectType: attribute.objectTypes[0],
                  direction: "in",
                }
              : null,
          )
        }
      />
      <Flex direction="column" minWidth="0">
        <Text size="2" weight="medium" truncate>
          {attribute.name}
        </Text>
        <Text size="1" color="gray" truncate>
          {attribute.activities.join(", ")}
        </Text>
      </Flex>
      {choice ? (
        <>
          <TextField.Root
            aria-label={`Flow of ${attribute.name}`}
            value={choice.flowId}
            onChange={(event) => onChange({ ...choice, flowId: event.target.value })}
          />
          <Select.Root
            value={choice.objectType}
            onValueChange={(objectType) => onChange({ ...choice, objectType })}
          >
            <Select.Trigger aria-label={`Where ${attribute.name} is measured`} variant="soft" />
            <Select.Content position="popper">
              {attribute.objectTypes.map((objectType) => (
                <Select.Item key={objectType} value={objectType}>
                  {objectType}
                </Select.Item>
              ))}
            </Select.Content>
          </Select.Root>
          <Select.Root
            value={choice.direction}
            onValueChange={(direction) =>
              onChange({ ...choice, direction: direction === "out" ? "out" : "in" })
            }
          >
            <Select.Trigger aria-label={`Direction of ${attribute.name}`} variant="soft" />
            <Select.Content position="popper">
              <Select.Item value="in">Into the object</Select.Item>
              <Select.Item value="out">Out of the object</Select.Item>
            </Select.Content>
          </Select.Root>
        </>
      ) : (
        <>
          <span />
          <span />
          <span />
        </>
      )}
    </>
  );
}
