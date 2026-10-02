import { GlobeIcon, RadarIcon, UsersIcon } from "lucide-react";
import type { AllocationRule } from "../../../../model/ocean/allocation";
import type { Choice } from "../../../../ui";

// How the allocation rules are offered.
export const allocationRules: Choice<AllocationRule>[] = [
  {
    value: "ParticipatingTargets",
    title: "Participating",
    description: "Split among the event's targets",
    icon: <UsersIcon size={16} />,
  },
  {
    value: "ClosestTargets",
    title: "Closest",
    description: "Nearest targets in the object graph",
    icon: <RadarIcon size={16} />,
  },
  {
    value: "AllTargets",
    title: "All",
    description: "Split among all targets",
    icon: <GlobeIcon size={16} />,
  },
];
