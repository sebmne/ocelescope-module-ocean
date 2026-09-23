// Identical to @ocelescope/core's pickers/types.ts, plus the types of the new
// pickers below the marker.

/** Which OCEL a picker reads its choices from. */
export interface OcelSource {
  /** Defaults to the OCEL the app has selected. */
  ocelId?: string;
  /** The unfiltered log, for choices that must not shift under a filter. */
  ocelVersion?: "filtered" | "original";
}

/** Picking one name, or none. */
export interface SinglePicker {
  multiple?: false;
  value: string | null | undefined;
  onChange: (value: string | undefined) => void;
}

/** Picking any number of names. */
export interface MultiPicker {
  multiple: true;
  value: readonly string[];
  onChange: (value: string[]) => void;
}

/** What a picker picks. Single unless it says otherwise. */
export type Selection = SinglePicker | MultiPicker;

/** The names as a set, which is how the pickers themselves hold them. */
export const chosen = (selection: Selection): Set<string> =>
  new Set(
    selection.multiple
      ? selection.value
      : selection.value == null
        ? []
        : [selection.value],
  );

/** Report a set back as the one name, or the list, the caller asked for. */
export const report = (selection: Selection, names: Iterable<string>) => {
  const list = [...names];
  if (selection.multiple) selection.onChange(list);
  else selection.onChange(list[0]);
};

// ---- Added for the new pickers ----------------------------------------------

/** How events of an activity relate to objects of a type, under one qualifier. */
export interface E2ORelation {
  objectType: string;
  qualifier: string;
}

/** An attribute of an activity's events, or of an object type's objects. */
export type AttributeRef =
  | { target: "event"; activity: string; name: string }
  | { target: "object"; objectType: string; name: string };
