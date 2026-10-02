import dynamic from "next/dynamic";
import type { HistogramChartProps } from "./HistogramChart";
import type { ScatterChartProps } from "./ScatterChart";

/**
 * Charts that @ocelescope/core does not have yet, written like its own (see
 * README.md): same props, drawn on the same plot.
 */

export type { HistogramChartProps } from "./HistogramChart";
export type { ScatterChartProps } from "./ScatterChart";

// Plotly reaches for `document` as it loads, so charts stay out of the server
// render - the same boundary core uses.
export const HistogramChart = dynamic<HistogramChartProps>(
  () => import("./HistogramChart").then((module) => module.HistogramChart),
  { ssr: false },
);

export const ScatterChart = dynamic<ScatterChartProps>(
  () => import("./ScatterChart").then((module) => module.ScatterChart),
  { ssr: false },
);
