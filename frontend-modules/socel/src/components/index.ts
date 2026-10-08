// The module's shared building blocks and its look: the only place that knows
// the component library (Radix Themes, via r4pm). Features build their screens
// from these. It holds what the pages use now: add a component, or a re-export,
// when a screen needs it.

// Shared with the rest of Ocelescope: the loading, empty and error states of
// anything asked from the backend.
// The colour a name has everywhere in Ocelescope, per scope ("activity",
// "objectType").
export { AsyncBoundary, useColorOf } from "@r4pm/components";
// Layout, typography and simple controls, as Radix provides them.
export {
  Badge,
  Box,
  Button,
  Code,
  Flex,
  Grid,
  IconButton,
  Progress,
  Select,
  Text,
  TextField,
  Tooltip,
} from "@r4pm/components/ui";
export { type BarNode, default as BarTree } from "./BarTree";
export { default as Page } from "./Page";
export { default as Section } from "./Section";
export { default as StatCards, type StatItem } from "./StatCards";
export { default as SubHeading } from "./SubHeading";
