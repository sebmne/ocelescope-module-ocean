import { CalendarIcon, WaypointsIcon } from "lucide-react";
import type { EmissionRuleType } from "../../../model/emissionRules";
import type { Choice } from "../../../ui";

// How the rule types are offered in the editor.
export const ruleTypes: Choice<EmissionRuleType>[] = [
  {
    value: "E",
    title: "Per event",
    description: "Every event of the activity emits once.",
    icon: <CalendarIcon size={16} />,
  },
  {
    value: "E2O",
    title: "Per related object",
    description: "Every event emits once for each object of a type it involves.",
    icon: <WaypointsIcon size={16} />,
  },
];
