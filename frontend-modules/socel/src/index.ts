import { defineModule, defineModuleRoute } from "@ocelescope/core";
import dynamic from "next/dynamic";
import WaveIcon from "./assets/WaveIcon";

// Pages are built from r4pm components, which load stylesheets and reach for
// `document` as they are imported: they stay out of the server render.
const OverviewPage = dynamic(() => import("./pages/OverviewPage"), { ssr: false });
const BuilderPage = dynamic(() => import("./pages/BuilderPage"), { ssr: false });

// The module's table of contents: every page, and how it appears in the navigation.
export default defineModule({
  name: "socel",
  label: "sOCEL",
  description: "Sustainability analysis of object-centric event logs.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "builder",
      label: "Builder",
      requiresOcel: true,
      component: BuilderPage,
    }),
    defineModuleRoute({
      name: "overview",
      label: "Overview",
      requiresOcel: ["socel"],
      component: OverviewPage,
    }),
  ],
  icon: WaveIcon,
});
