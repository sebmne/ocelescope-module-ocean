import type { CartesianChartProps } from "@ocelescope/core";
import { axis, Plot } from "./internal/Plot";

export interface ScatterChartProps extends Omit<CartesianChartProps, "y" | "colorOf"> {
  /** Column holding the vertical value; `x` holds the horizontal one. */
  y: string;
  /** Column naming each point: shown on hover and reported on a click. */
  label: string;
  /** Column that, when true, draws a point hollow - e.g. one nested in another. */
  hollow?: string;
  /** Colour for a series; none keeps the default one. */
  colorOf?: (name: string) => string | undefined;
  /** Draw the line y = x, e.g. where all of a total was accounted for. */
  diagonal?: boolean;
  /** How a value reads on hover. */
  format?: (value: number) => string;
  /** The point to ring, by its label. */
  selected?: string;
}

/**
 * Points by two values, one per row, coloured by `series`. Unlike core's
 * ScatterChart, every point carries a name of its own - it is what a click
 * reports - and the line y = x can be drawn for reference.
 */
export const ScatterChart = ({
  rows,
  x,
  y,
  series,
  label,
  hollow,
  colorOf,
  onSelect,
  xRange,
  diagonal = false,
  format = (value) => value.toLocaleString(undefined, { maximumFractionDigits: 2 }),
  selected,
}: ScatterChartProps) => {
  const groups = Map.groupBy(rows, (row) => (series ? String(row[series] ?? "∅") : y));
  const traces: object[] = [...groups].map(([name, group]) => {
    const color = colorOf?.(name);
    return {
      type: "scattergl",
      mode: "markers",
      name,
      x: group.map((row) => Number(row[x] ?? 0)),
      y: group.map((row) => Number(row[y] ?? 0)),
      text: group.map((row) => String(row[label] ?? "")),
      customdata: group.map((row) => [format(Number(row[x] ?? 0)), format(Number(row[y] ?? 0))]),
      marker: {
        size: group.map((row) => (String(row[label]) === selected ? 14 : 9)),
        symbol: group.map((row) => (hollow && row[hollow] ? "circle-open" : "circle")),
        line: {
          width: group.map((row) => (String(row[label]) === selected ? 3 : 1.5)),
          ...(color && { color }),
        },
        opacity: 0.85,
        ...(color && { color }),
      },
      hovertemplate: `<b>%{text}</b><br>${x}: %{customdata[0]}<br>${y}: %{customdata[1]}<extra>%{fullData.name}</extra>`,
    };
  });

  if (diagonal && rows.length > 0) {
    const values = rows.flatMap((row) => [Number(row[x] ?? 0), Number(row[y] ?? 0)]);
    const low = Math.min(0, ...values);
    const high = Math.max(0, ...values);
    traces.unshift({
      type: "scatter",
      mode: "lines",
      x: [low, high],
      y: [low, high],
      line: { dash: "dot", width: 1, color: "rgba(128, 128, 128, 0.6)" },
      hoverinfo: "skip",
      showlegend: false,
    });
  }

  return (
    <Plot
      traces={traces}
      legend={groups.size > 1}
      readName={(point) => String(point.text ?? "")}
      onSelect={onSelect}
      layout={{
        hovermode: "closest",
        xaxis: { ...axis(x, xRange), zeroline: true },
        yaxis: { ...axis(y), zeroline: true },
      }}
    />
  );
};
