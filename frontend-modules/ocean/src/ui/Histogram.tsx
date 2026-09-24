import { BarChart } from "@ocelescope/core";
import { Box } from "@r4pm/components/ui";

export interface Bin {
  from: number;
  to: number;
  count: number;
}

interface HistogramProps {
  bins: readonly Bin[];
  /** How a bin bound is shown, e.g. "4.7 kg". */
  formatBound: (value: number) => string;
  /** Title of the value axis, e.g. "kg CO₂e per object". */
  valueLabel: string;
  /** Title of the count axis, e.g. "Objects". */
  countLabel: string;
  height?: number;
}

// How values are distributed: one bar per bin, its height the count.
// Ocelescope's own (Plotly) bar chart, so it hovers and zooms like every other
// chart in the app; the column names become the axis titles.
export default function Histogram({
  bins,
  formatBound,
  valueLabel,
  countLabel,
  height = 260,
}: HistogramProps) {
  const rows = bins.map((bin) => ({
    [valueLabel]: `${formatBound(bin.from)} – ${formatBound(bin.to)}`,
    [countLabel]: bin.count,
  }));

  // The chart fills its parent, so the parent needs a height.
  return (
    <Box style={{ height }}>
      <BarChart rows={rows} x={valueLabel} y={countLabel} />
    </Box>
  );
}
