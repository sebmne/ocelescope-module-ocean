import { defineModule, defineModuleRoute } from "@ocelescope/core";
import WaveIcon from "./assets/WaveIcon";
import Emissions from "./routes/Emissions";

export default defineModule({
  name: "ocean",
  label: "OCEAN",
  description: "Object-centric emission analysis: assign emissions to events and allocate them to objects.",
  authors: [{ name: "Menne, Sebastian" }],
  routes: [
    defineModuleRoute({
      name: "emissions",
      label: "Emissions",
      requiresOcel: true,
      component: Emissions,
    }),
  ],
  icon: WaveIcon,
});
