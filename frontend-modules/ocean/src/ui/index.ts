// OCEAn's UI layer: the only place that knows the component library (Radix
// Themes, via r4pm). Features build their screens from these.

// Layout, typography and simple controls, as Radix provides them.
export {
  Badge,
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  IconButton,
  Separator,
  Spinner,
  Strong,
  Table,
  Text,
  Tooltip,
  VisuallyHidden,
} from "@r4pm/components/ui";

export { type Choice, default as ChoiceCards } from "./ChoiceCards";
export { default as ClickableRow } from "./ClickableRow";
export { default as EmptyState } from "./EmptyState";
export { default as Field } from "./Field";
export { default as FieldGroup } from "./FieldGroup";
export { type Bin, default as Histogram } from "./Histogram";
export { default as Notice } from "./Notice";
export { default as NumberField } from "./NumberField";
export { default as OceanTheme } from "./OceanTheme";
export { default as Page } from "./Page";
export { default as Panel } from "./Panel";
export { default as ProportionBar, type Proportion } from "./ProportionBar";
export { default as Section } from "./Section";
export { default as SideSheet } from "./SideSheet";
export { default as Stat } from "./Stat";
export { default as StatusBadge, type Status, type StatusTone } from "./StatusBadge";
export { default as SwitchField } from "./SwitchField";
