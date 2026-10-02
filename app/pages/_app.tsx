// The only stylesheet the app needs: it inlines the third-party global CSS that
// core and the Ocelescope modules rely on (Mantine and its extensions,
// mantine-datatable, @xyflow/react, @r4pm/components) ahead of core's own styles,
// in cascade order. A module that ships its own stylesheet is imported after it.
import "@ocelescope/core/styles.css";

import { OcelescopeApp } from "@ocelescope/core";
import config from "../ocelescope.config";

export default OcelescopeApp(config);
