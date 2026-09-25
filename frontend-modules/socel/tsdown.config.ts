import { defineConfig } from "tsdown";

export default defineConfig({
  entry: ["src/index.ts"],
  dts: true,
  format: ["esm"],
  // Emit dist/index.js (not .mjs) so it matches "exports" in package.json.
  fixedExtension: false,
});
