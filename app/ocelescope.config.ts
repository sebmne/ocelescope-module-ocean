import type { OcelescopeConfig } from "@ocelescope/core";
import management from "@ocelescope/management";
import socel from "@instance/socel-module";

export default {
  modules: [management, socel],
  navbarGroups: [{ title: "Core", modulesNames: [management.name] }],
} satisfies OcelescopeConfig;
