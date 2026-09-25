// The frontend's architecture, enforced (the counterpart of the backend's
// import-linter contracts). Run: pnpm --filter @instance/socel-module check:architecture
//
// Like the backend, the module is made of page slices (for now OCEAn, `ocean/`):
// features/, data/ and model/ group their code per page, e.g. features/ocean/.
// Files directly in data/ or model/ are shared by all pages.
//
//   index.ts     the module's pages and navigation
//   routes/      one file per route: a Page composing features
//   features/    self-contained capabilities per page, each with an index.ts as its entry
//   data/        the only place that talks to the backend (generated api/)
//   model/       the frontend's state as pure types and functions
//   ui/          the module's design language: the only place that knows the component library
//   components/  generic UI with its own life, e.g. the pickers
//   lib/         technical helpers
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    // ---- Routes, page slices and features -----------------------------------
    {
      name: "features-do-not-know-routes",
      comment: "Routes compose features; a feature never depends on a route.",
      severity: "error",
      from: { path: "^src/features/" },
      to: { path: "^src/routes/" },
    },
    {
      name: "features-are-independent",
      comment:
        "A feature does not import another feature. Features connect through data/ " +
        "(e.g. results read what the rules computed) and model/.",
      severity: "error",
      from: { path: "^src/features/([^/]+/[^/]+)/" },
      to: { path: "^src/features/", pathNot: "^src/features/$1/" },
    },
    {
      name: "features-only-through-their-entry",
      comment: "Outside a feature, only its index.ts may be imported; its insides are private.",
      severity: "error",
      from: { pathNot: "^src/features/" },
      to: {
        path: "^src/features/[^/]+/[^/]+/.+",
        pathNot: "^src/features/[^/]+/[^/]+/index\\.ts$",
      },
    },
    {
      name: "page-slices-are-independent",
      comment:
        "One page's features, data and model do not reach into another page's. " +
        "What pages share lives directly in data/, model/, ui/, components/ or lib/.",
      severity: "error",
      from: { path: "^src/(?:features|data|model)/([^/]+)/" },
      to: {
        path: "^src/(?:features|data|model)/[^/]+/",
        pathNot: "^src/(?:features|data|model)/$1/",
      },
    },

    // ---- Layers -------------------------------------------------------------
    {
      name: "api-only-through-data",
      comment: "Only data/ uses the generated client; everything else asks data/.",
      severity: "error",
      from: { path: "^src/", pathNot: "^src/(data|api)/" },
      to: { path: "^src/api/" },
    },
    {
      name: "model-is-pure",
      comment: "model/ holds plain types and functions: no React, no backend, no screens.",
      severity: "error",
      from: { path: "^src/model/" },
      to: {
        path: [
          "^src/(api|data|routes|features|ui|lib)/",
          "(^|/)node_modules/(react|react-dom|@tanstack|@mantine|@radix-ui)/",
        ],
      },
    },
    {
      name: "data-knows-no-ui",
      comment: "data/ serves the screens but does not know them.",
      severity: "error",
      from: { path: "^src/data/" },
      to: { path: "^src/(routes|features|ui|components)/" },
    },
    {
      name: "ui-is-design-only",
      comment: "ui/ is the design language: no data access, no state of the app, no screens.",
      severity: "error",
      from: { path: "^src/ui/" },
      to: { path: "^src/(routes|features|data|model|api)/" },
    },
    {
      name: "components-are-generic",
      comment: "components/ can be used by any feature: no screens, data access or app state.",
      severity: "error",
      from: { path: "^src/components/" },
      to: { path: "^src/(routes|features|data|model)/" },
    },
    {
      name: "component-library-only-in-ui",
      comment:
        "Screens are built from ui/, which alone knows Radix (via r4pm) and Mantine. " +
        "The pickers are exempt: they are their own library, meant for Ocelescope core.",
      severity: "error",
      from: { path: "^src/", pathNot: "^src/(ui|components/pickers)/" },
      to: {
        path: [
          "(^|/)node_modules/@mantine/",
          "(^|/)node_modules/@radix-ui/",
          "(^|/)node_modules/@r4pm/components/dist/ui/",
        ],
      },
    },
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default", "types"],
    },
  },
};
