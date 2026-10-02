import { defineModule, defineModuleRoute } from "@ocelescope/core";
import WaveIcon from "./assets/WaveIcon";
import OverviewPage from "./routes/OverviewPage";

// The module's table of contents: every page, and how it appears in the navigation.
export default defineModule({
  name: "socel",
  label: "sOCEL",
  description: "Sustainability analysis of object-centric event logs.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "overview",
      label: "Overview",
      requiresOcel: true,
      requiresExtensions: ["socel"],
      component: OverviewPage,
    }),
  ],
  icon: WaveIcon,
});
