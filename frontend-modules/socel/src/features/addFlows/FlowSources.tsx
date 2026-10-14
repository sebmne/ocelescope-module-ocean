import { FileSpreadsheetIcon, TagsIcon } from "lucide-react";
import { type ReactNode, useRef, useState } from "react";
import { Button, Flex, Grid, Text } from "../../components";

interface FlowSourcesProps {
  isUploading: boolean;
  error: Error | null;
  onFile: (file: File) => void;
  onAttributes: () => void;
}

// Where the flows come from: a CSV, dropped or chosen, or the attributes of
// the log's events.
export default function FlowSources({
  isUploading,
  error,
  onFile,
  onAttributes,
}: FlowSourcesProps) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  return (
    <Flex direction="column" gap="3">
      <Grid columns={{ initial: "1", md: "2" }} gap="4">
        <Choice
          icon={<FileSpreadsheetIcon size={28} />}
          title="CSV file"
          highlighted={over}
          onDragOver={() => setOver(true)}
          onDragLeave={() => setOver(false)}
          onDrop={(file) => {
            setOver(false);
            onFile(file);
          }}
        >
          <input
            ref={input}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(event) => {
              const chosen = event.target.files?.[0];
              if (chosen) onFile(chosen);
              event.target.value = "";
            }}
          />
          <Text size="2" color="gray">
            Drop it here, or
          </Text>
          <Button variant="soft" onClick={() => input.current?.click()} loading={isUploading}>
            Choose a file
          </Button>
        </Choice>
        <Choice icon={<TagsIcon size={28} />} title="Event attributes">
          <Text size="2" color="gray">
            Numbers on the log's events
          </Text>
          <Button variant="soft" onClick={onAttributes}>
            Choose attributes
          </Button>
        </Choice>
      </Grid>
      {error && (
        <Text size="2" color="red">
          {error.message}
        </Text>
      )}
    </Flex>
  );
}

function Choice({
  icon,
  title,
  highlighted = false,
  onDragOver,
  onDragLeave,
  onDrop,
  children,
}: {
  icon: ReactNode;
  title: string;
  highlighted?: boolean;
  onDragOver?: () => void;
  onDragLeave?: () => void;
  onDrop?: (file: File) => void;
  children: ReactNode;
}) {
  return (
    <Flex
      direction="column"
      align="center"
      justify="center"
      gap="3"
      py="8"
      onDragOver={(event) => {
        if (!onDrop) return;
        event.preventDefault();
        onDragOver?.();
      }}
      onDragLeave={onDragLeave}
      onDrop={(event) => {
        if (!onDrop) return;
        event.preventDefault();
        const dropped = event.dataTransfer.files[0];
        if (dropped) onDrop(dropped);
      }}
      style={{
        border: `1px dashed ${highlighted ? "var(--accent-8)" : "var(--gray-a7)"}`,
        borderRadius: "var(--radius-4)",
        background: highlighted ? "var(--accent-a2)" : "var(--color-panel-solid)",
        minHeight: 220,
      }}
    >
      <Flex style={{ color: "var(--gray-10)" }}>{icon}</Flex>
      <Text size="4" weight="medium">
        {title}
      </Text>
      {children}
    </Flex>
  );
}

/** A small button that adds a CSV file once flows are set up already. */
export function AddFile({
  isUploading,
  onFile,
}: {
  isUploading: boolean;
  onFile: (file: File) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={input}
        type="file"
        accept=".csv,text/csv"
        hidden
        onChange={(event) => {
          const chosen = event.target.files?.[0];
          if (chosen) onFile(chosen);
          event.target.value = "";
        }}
      />
      <Button
        variant="soft"
        color="gray"
        onClick={() => input.current?.click()}
        loading={isUploading}
      >
        <FileSpreadsheetIcon size={15} />
        Add a CSV file
      </Button>
    </>
  );
}
