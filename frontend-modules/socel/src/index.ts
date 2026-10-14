import { defineModule, defineModuleRoute } from "@ocelescope/core";
import dynamic from "next/dynamic";
import WaveIcon from "./assets/WaveIcon";

// Pages are built from r4pm components, which load stylesheets and reach for
// `document` as they are imported: they stay out of the server render.
const OverviewPage = dynamic(() => import("./pages/OverviewPage"), { ssr: false });
const ConfigPage = dynamic(() => import("./pages/ConfigPage"), { ssr: false });
const NewSocelPage = dynamic(() => import("./pages/NewSocelPage"), { ssr: false });

// The module's table of contents: every page, and how it appears in the navigation.
export default defineModule({
  name: "ocean",
  label: "OCEAn",
  description: "Object-centric emission analysis.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "new",
      label: "New sOCEL",
      requiresOcel: true,
      component: NewSocelPage,
    }),
    defineModuleRoute({
      name: "config",
      label: "sOCEL config",
      requiresOcel: ["socel"],
      component: ConfigPage,
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
