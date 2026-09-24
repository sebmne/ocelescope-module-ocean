import { GlobeIcon, RadarIcon, UsersIcon } from "lucide-react";
import type { AllocationRule } from "../../../model/allocation";
import type { Choice } from "../../../ui";

// How the allocation rules are offered.
export const allocationRules: Choice<AllocationRule>[] = [
  {
    value: "ParticipatingTargets",
    title: "Participating",
    description: "An event's emissions are split evenly among the target objects it involves.",
    icon: <UsersIcon size={16} />,
  },
  {
    value: "ClosestTargets",
    title: "Closest",
    description: "An event's emissions go to the nearest target objects in the object graph.",
    icon: <RadarIcon size={16} />,
  },
  {
    value: "AllTargets",
    title: "All",
    description: "All emissions are split evenly among all target objects.",
    icon: <GlobeIcon size={16} />,
  },
];
