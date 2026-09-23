import type { OcelescopeConfig } from "@ocelescope/core";
import management from "@ocelescope/management";
import ocean from "@instance/ocean-module";

export default {
  modules: [management, ocean],
  navbarGroups: [{ title: "Core", modulesNames: [management.name] }],
} satisfies OcelescopeConfig;
