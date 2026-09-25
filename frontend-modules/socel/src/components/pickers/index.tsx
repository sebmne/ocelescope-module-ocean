import dynamic from "next/dynamic";
import type { ActivityPickerProps } from "./ActivityPicker";
import type { E2ORelationPickerProps } from "./E2ORelationPicker";
import type { EventAttributePickerProps } from "./EventAttributePicker";
import type { NamePickerProps } from "./NamePicker";
import type { ObjectAttributePickerProps } from "./ObjectAttributePicker";
import type { ObjectTypePickerProps } from "./ObjectTypePicker";
import type { RelatedAttributePickerProps } from "./RelatedAttributePicker";
import type { Selection } from "./types";

/**
 * Picking names out of an OCEL. Mirrors @ocelescope/core's pickers (see
 * README.md): same exports and props, plus optional additions.
 *
 * Two layers, so that either can be used on its own: `NamePicker` is
 * presentational - handed what to offer, it reports what was picked - and one
 * picker per endpoint wraps it around the OCEL module's counts and attributes.
 */

export type { ActivityPickerProps } from "./ActivityPicker";
export type { E2ORelationPickerProps } from "./E2ORelationPicker";
export type { EventAttributePickerProps } from "./EventAttributePicker";
export type { NameItem, NamePickerProps } from "./NamePicker";
export type { ObjectAttributePickerProps } from "./ObjectAttributePicker";
export type { ObjectTypePickerProps } from "./ObjectTypePicker";
export type { RelatedAttributePickerProps } from "./RelatedAttributePicker";
export type {
  AttributeRef,
  E2ORelation,
  MultiPicker,
  OcelSource,
  Selection,
  SinglePicker,
} from "./types";

// Everything built on r4pm reaches for `document` as it loads, so it stays out
// of the server render - the same boundary core uses.
export const NamePicker = dynamic<NamePickerProps & Selection>(
  () => import("./NamePicker").then((module) => module.NamePicker),
  { ssr: false },
);

export const ActivityPicker = dynamic<ActivityPickerProps & Selection>(
  () => import("./ActivityPicker").then((module) => module.ActivityPicker),
  { ssr: false },
);

export const ObjectTypePicker = dynamic<ObjectTypePickerProps & Selection>(
  () => import("./ObjectTypePicker").then((module) => module.ObjectTypePicker),
  { ssr: false },
);

export const EventAttributePicker = dynamic<EventAttributePickerProps & Selection>(
  () => import("./EventAttributePicker").then((module) => module.EventAttributePicker),
  { ssr: false },
);

export const ObjectAttributePicker = dynamic<ObjectAttributePickerProps & Selection>(
  () => import("./ObjectAttributePicker").then((module) => module.ObjectAttributePicker),
  { ssr: false },
);

export const E2ORelationPicker = dynamic<E2ORelationPickerProps>(
  () => import("./E2ORelationPicker").then((module) => module.E2ORelationPicker),
  { ssr: false },
);

export const RelatedAttributePicker = dynamic<RelatedAttributePickerProps>(
  () => import("./RelatedAttributePicker").then((module) => module.RelatedAttributePicker),
  { ssr: false },
);
