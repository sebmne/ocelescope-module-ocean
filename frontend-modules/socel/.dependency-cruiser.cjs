// The frontend's structure, enforced.
// Run: pnpm --filter @instance/socel-module check:architecture
//
// Code is grouped by feature: a feature folder holds its components, its hooks
// and its helpers together. What several features need moves up into the shared
// folders.
//
//   index.ts      the module's pages and navigation
//   pages/        one file per page, composing features
//   features/     one folder per feature, everything it needs inside
//   components/   the shared building blocks and the module's look
//   hooks/        shared hooks
//   lib/          generic helpers
//   api/          the generated backend client
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "features-are-independent",
      comment:
        "A feature does not import another feature. What two features share moves " +
        "to components/, hooks/ or lib/.",
      severity: "error",
      from: { path: "^src/features/([^/]+)/" },
      to: { path: "^src/features/", pathNot: "^src/features/$1/" },
    },
    {
      name: "shared-code-knows-no-feature",
      comment: "components/, hooks/ and lib/ serve the features and pages, never the reverse.",
      severity: "error",
      from: { path: "^src/(components|hooks|lib)/" },
      to: { path: "^src/(features|pages)/" },
    },
    {
      name: "component-library-only-in-components",
      comment:
        "Only components/ imports Radix (via r4pm) and Mantine, so the look stays in " +
        "one place. Pickers and charts come from @ocelescope/core.",
      severity: "error",
      from: { path: "^src/", pathNot: "^src/components/" },
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
