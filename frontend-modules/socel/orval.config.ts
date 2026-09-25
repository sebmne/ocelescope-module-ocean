import { defineConfig } from "@ocelescope/api-config";

// `defineConfig` applies Ocelescope's shared Orval defaults: react-query hooks
// over axios, input ./openapi.json (written by `pnpm run generate:api` from the
// sOCEL backend module), and src/lib/fetcher.ts as the request function.
export default defineConfig({
  socel: {
    output: { target: "./src/api/socel.ts" },
  },
});
