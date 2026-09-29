import { BarChart } from "@ocelescope/core";
import { Box } from "@r4pm/components/ui";

export interface TimeBar {
  /** The window's middle, as an ISO timestamp. */
  at: string;
  value: number;
  /** The part of a stack the value belongs to. */
  series: string;
}

interface TimeBarsProps {
  bars: readonly TimeBar[];
  /** Title of the value axis, e.g. "m3". */
  valueLabel: string;
  /** Title of the legend, e.g. "Meter". */
  seriesLabel: string;
  height?: number;
}

// Values over time as stacked bars, one stack per window. Ocelescope's own
// (Plotly) chart, so it hovers and zooms like every other chart in the app.
export default function TimeBars({ bars, valueLabel, seriesLabel, height = 280 }: TimeBarsProps) {
  const rows = bars.map((bar) => ({
    Time: bar.at,
    [valueLabel]: bar.value,
    [seriesLabel]: bar.series,
  }));
  return (
    <Box style={{ height }}>
      <BarChart rows={rows} x="Time" y={valueLabel} series={seriesLabel} stacked />
    </Box>
  );
}
