import { ThemedPlot } from "@r4pm/components/charts";
import type { ComponentType, CSSProperties } from "react";

// A copy of core's `internal/Plot.tsx` (not exported by @ocelescope/core), so the
// charts here look like core's. When moving to core: delete, and use core's.

/** What a click reports: the point, and the trace it belongs to. */
export interface PlotPoint {
  x?: unknown;
  y?: unknown;
  label?: unknown;
  text?: unknown;
  data: { name?: string };
}

interface PlotProps {
  traces: object[];
  layout?: object;
  legend?: boolean;
  readName?: (point: PlotPoint) => string;
  onSelect?: (name: string, point: unknown) => void;
}

interface ThemedPlotProps {
  data: object[];
  layout: object;
  config: object;
  style: CSSProperties;
  useResizeHandler: boolean;
  onClick: (event: { points: readonly PlotPoint[] }) => void;
}

// r4pm's types come from react-plotly.js, which this package does not install.
const Themed = ThemedPlot as unknown as ComponentType<ThemedPlotProps>;

/**
 * The plot every chart draws on: r4pm's themed Plotly, with the parts that
 * should look the same everywhere - margins, legend, no mode bar - already set.
 */
export const Plot = ({
  traces,
  layout,
  legend = false,
  readName = (point) => String(point?.label ?? point?.x ?? ""),
  onSelect,
}: PlotProps) => (
  <Themed
    data={traces}
    layout={{
      autosize: true,
      margin: { t: legend ? 44 : 12, r: 16, b: 48, l: 56, pad: 2 },
      showlegend: legend,
      clickmode: onSelect ? "event+select" : "event",
      legend: {
        orientation: "h",
        y: 1.02,
        yref: "paper",
        yanchor: "bottom",
        x: 0,
        xanchor: "left",
        bgcolor: "rgba(0,0,0,0)",
      },
      hoverlabel: { namelength: -1 },
      ...layout,
    }}
    config={{
      displaylogo: false,
      displayModeBar: false,
      responsive: true,
      scrollZoom: false,
      doubleClick: "reset",
    }}
    style={{ width: "100%", height: "100%" }}
    useResizeHandler
    onClick={({ points }) => points[0] && onSelect?.(readName(points[0]), points[0])}
  />
);

/** An axis that keeps its labels on screen, named after its column. */
export const axis = (title?: string, range?: readonly [unknown, unknown]) => ({
  automargin: true,
  ticks: "outside",
  ticklen: 4,
  tickfont: { size: 11 },
  zeroline: false,
  ...(title && { title: { text: title, font: { size: 12 }, standoff: 10 } }),
  ...(range && { range: [...range] }),
});
