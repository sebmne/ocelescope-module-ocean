import { defineModule, defineModuleRoute } from "@ocelescope/core";
import WaveIcon from "./assets/WaveIcon";
import OceanPage from "./routes/OceanPage";

// The module's table of contents: every page, and how it appears in the navigation.
export default defineModule({
  name: "socel",
  label: "sOCEL",
  description:
    "Sustainability analysis of object-centric event logs. Includes OCEAn, the object-centric emission analysis adapted from works by Raimund Hensen.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "ocean",
      label: "OCEAn",
      requiresOcel: true,
      component: OceanPage,
    }),
  ],
  icon: WaveIcon,
});
