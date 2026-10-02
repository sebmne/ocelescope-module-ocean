import type { CartesianChartProps, Row } from "@ocelescope/core";
import { useLayoutEffect, useRef, useState } from "react";
import { axis, Plot } from "./internal/Plot";

export interface HistogramChartProps extends Omit<CartesianChartProps, "colorOf"> {
  /** Colour for a series; none keeps the default one - so a single series,
   * e.g. a rest, can stand out without colouring all of them. */
  colorOf?: (name: string) => string | undefined;
  /** Column holding each bin's upper bound; `x` holds its lower bound. Both
   * numbers, or both timestamps (zone-less ones read as UTC). */
  xEnd: string;
  /** Show the legend. By default when there is more than one series. */
  legend?: boolean;
  /** How a bin bound reads on hover (timestamps as ms). By default the number,
   * or the timestamp to the minute. */
  formatBound?: (value: number) => string;
}

interface Bin {
  from: number;
  to: number;
  value: number;
}

/**
 * Values over bins as a histogram: every bar spans its bin, from `x` to `xEnd`,
 * so bins of any width - a day, an hour, 0-5 kg - sit where they belong and
 * touch their neighbours. Several series stack within a bin; negative values
 * stack below the axis.
 */
export const HistogramChart = ({
  rows,
  x,
  xEnd,
  y,
  series,
  colorOf,
  onSelect,
  xRange,
  legend,
  formatBound,
}: HistogramChartProps) => {
  const measure = (Array.isArray(y) ? y[0] : y) ?? "";
  const temporal = rows.some((row) => typeof row[x] !== "number");
  const groups = toGroups(rows, { x, xEnd, y, series, temporal });
  const edge = useEdgeColor();

  const totals = new Map<number, number>();
  for (const group of groups) {
    for (const bin of group.bins) totals.set(bin.from, (totals.get(bin.from) ?? 0) + bin.value);
  }

  const traces = groups.map((group) => ({
    type: "bar",
    name: group.name,
    x: group.bins.map((bin) => (temporal ? new Date(bin.from).toISOString() : bin.from)),
    y: group.bins.map((bin) => bin.value),
    width: group.bins.map((bin) => bin.to - bin.from),
    offset: 0,
    customdata: group.bins.map((bin) => {
      const total = totals.get(bin.from) ?? 0;
      return [
        formatBound ? formatBound(bin.from) : bound(bin.from, temporal),
        formatBound ? formatBound(bin.to) : bound(bin.to, temporal),
        total !== 0 ? bin.value / total : 0,
      ];
    }),
    marker: {
      line: { width: 1, color: edge.color },
      ...(colorOf?.(group.name) && { color: colorOf(group.name) }),
    },
    hovertemplate:
      `<b>%{customdata[0]} – %{customdata[1]}</b><br>${measure}: %{y}` +
      (groups.length > 1 ? "<br>Share: %{customdata[2]:.1%}" : "") +
      "<extra>%{fullData.name}</extra>",
  }));

  return (
    <div ref={edge.ref} style={{ width: "100%", height: "100%" }}>
      <Plot
        traces={traces}
        legend={legend ?? groups.length > 1}
        readName={(point) => point.data.name ?? ""}
        onSelect={onSelect}
        layout={{
          barmode: "relative",
          bargap: 0,
          hovermode: "closest",
          xaxis: { ...axis(x, xRange), type: temporal ? "date" : "linear" },
          yaxis: { ...axis(measure), ...countTicks(groups) },
        }}
      />
    </div>
  );
};

/** The rows as series of bins: one per value of the `series` column, or one per measure. */
function toGroups(
  rows: readonly Row[],
  {
    x,
    xEnd,
    y,
    series,
    temporal,
  }: {
    x: string;
    xEnd: string;
    y: string | readonly string[];
    series?: string;
    temporal: boolean;
  },
) {
  const measures = Array.isArray(y) ? y : [y];
  const at = (value: unknown) => (temporal ? instant(value) : Number(value));
  const binOf = (row: Row, measure: string): Bin => ({
    from: at(row[x]),
    to: at(row[xEnd]),
    value: Number(row[measure] ?? 0),
  });

  if (!series) {
    return measures.map((measure) => ({
      name: measure,
      bins: rows.map((row) => binOf(row, measure)),
    }));
  }
  const groups = new Map<string, Bin[]>();
  for (const row of rows) {
    const name = row[series] == null ? "∅" : String(row[series]);
    groups.set(name, [...(groups.get(name) ?? []), binOf(row, measures[0] ?? "")]);
  }
  return [...groups].map(([name, bins]) => ({ name, bins }));
}

/**
 * Whole-number ticks for counts: when every value is whole, the axis steps by
 * one while the stacks stay low (Plotly would tick 0.5, 1, 1.5), and rounds
 * its labels beyond that.
 */
function countTicks(groups: readonly { bins: readonly Bin[] }[]) {
  const values = groups.flatMap((group) => group.bins.map((bin) => bin.value));
  if (!values.every(Number.isInteger)) return {};
  const stacks = new Map<number, number>();
  for (const group of groups) {
    for (const bin of group.bins) {
      stacks.set(bin.from, (stacks.get(bin.from) ?? 0) + Math.abs(bin.value));
    }
  }
  const highest = Math.max(0, ...stacks.values());
  return highest <= 10 ? { dtick: 1, tickformat: "d" } : { tickformat: "d" };
}

/** A timestamp in ms; one without a zone is read as UTC, like Plotly shows it. */
function instant(value: unknown) {
  if (value instanceof Date) return value.getTime();
  const text = String(value);
  return Date.parse(/(Z|[+-]\d\d:?\d\d)$/.test(text) ? text : `${text}Z`);
}

/** A bin bound as the hover shows it. */
function bound(value: number, temporal: boolean) {
  return temporal ? new Date(value).toISOString().slice(0, 16).replace("T", " ") : String(value);
}

/**
 * The colour bins are edged in: the background's, so neighbours stay apart in
 * light and dark themes. Read from the theme around the chart (Radix, then Mantine).
 */
function useEdgeColor() {
  const ref = useRef<HTMLDivElement>(null);
  const [color, setColor] = useState("rgba(255,255,255,0.9)");
  useLayoutEffect(() => {
    if (!ref.current) return;
    const style = getComputedStyle(ref.current);
    const background = ["--color-panel-solid", "--mantine-color-body"]
      .map((name) => style.getPropertyValue(name).trim())
      .find(Boolean);
    if (background) setColor(background);
  }, []);
  return { ref, color };
}
