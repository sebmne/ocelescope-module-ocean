import { useState } from "react";
import {
  type ColumnMapping,
  type RecordFilePreview,
  type UploadedRecordFile,
  usePreviewRecordFile,
  useUploadRecordFile,
} from "../../api/socel";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";

export type RecordFile = UploadedRecordFile;
export type { RecordIssue } from "../../api/socel";
export type Preview = RecordFilePreview;
export type Mapping = ColumnMapping;
/** What a column of the file can hold. */
export type Role = keyof Mapping;

/** Whether the mapping names enough columns to read the file: for records
 * flow, object and quantity, and either start and end or the event; for the end
 * times of events alone the event and the end. */
export function canBeRead(mapping: Mapping) {
  const records =
    !!mapping.flow &&
    !!mapping.object &&
    !!mapping.quantity &&
    (!!mapping.event || (!!mapping.startTime && !!mapping.endTime));
  const eventEnds = !!mapping.event && !!mapping.endTime;
  return records || eventEnds;
}

/**
 * The record file uploaded for the selected log: its columns, which of them
 * holds what as the user says, and what the file holds when read that way.
 */
export function useRecordFile() {
  const { ocelId } = useSelectedOcel();
  const uploading = useUploadRecordFile<Error>();
  const previewing = usePreviewRecordFile<Error>();
  const [file, setFile] = useState<RecordFile>();
  const [name, setName] = useState<string>();
  const [mapping, setMapping] = useState<Mapping>({});
  const [preview, setPreview] = useState<Preview | null>(null);

  const upload = (chosen: File) =>
    uploading.mutate(
      { ocelId, data: { file: chosen } },
      {
        onSuccess: (uploaded) => {
          setFile(uploaded);
          setName(chosen.name);
          setMapping({});
          setPreview(null);
        },
      },
    );

  /** Says what a column holds; a role another column had moves to this one. */
  const assign = (column: string, role: Role | null) => {
    if (!file) return;
    const next: Mapping = Object.fromEntries(
      Object.entries(mapping).map(([key, name]) => [key, name === column ? null : name]),
    );
    if (role) next[role] = column;
    setMapping(next);
    if (!canBeRead(next)) {
      setPreview(null);
      return;
    }
    previewing.mutate(
      { ocelId, uploadId: file.uploadId, data: next },
      { onSuccess: setPreview, onError: () => setPreview(null) },
    );
  };

  const remove = () => {
    setFile(undefined);
    setName(undefined);
    setMapping({});
    setPreview(null);
  };

  return {
    file,
    name,
    mapping,
    preview,
    upload,
    assign,
    remove,
    isUploading: uploading.isPending,
    isReading: previewing.isPending,
    error: uploading.error ?? previewing.error,
  };
}
