import { defineModule, defineModuleRoute } from "@ocelescope/core";
import WaveIcon from "./assets/WaveIcon";
import EmissionsPage from "./routes/EmissionsPage";

// The module's table of contents: every page, and how it appears in the navigation.
export default defineModule({
  name: "ocean",
  label: "OCEAn",
  description:
    "Object-centric emission analysis: assign emissions to events and allocate them to objects. Adapted from works by Raimund Hensen.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "emissions",
      label: "Emissions",
      requiresOcel: true,
      component: EmissionsPage,
    }),
  ],
  icon: WaveIcon,
});
