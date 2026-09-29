import { ChartColumnIcon } from "lucide-react";
import { useState } from "react";
import type { FlowAttribution } from "../../../data/analysis/useAttribution";
import { type Bucket, useFlowSeries } from "../../../data/analysis/useFlowSeries";
import { parseUtc } from "../../../lib/format";
import { BUCKET_LABELS, BUCKETS } from "../../../model/analysis/buckets";
import { EmptyState, Flex, Section, SegmentedControl, Spinner, TimeBars } from "../../../ui";

interface FlowSeriesSectionProps {
  step: number;
  flow: FlowAttribution;
  defaultBucket: Bucket;
}

// The flow over time: its quantity per window, stacked by meter (nested meters left out).
export default function FlowSeriesSection({ step, flow, defaultBucket }: FlowSeriesSectionProps) {
  const [bucket, setBucket] = useState<Bucket>(defaultBucket);
  const { data: series } = useFlowSeries(flow.flowId, bucket);

  return (
    <Section
      step={step}
      title="Quantities over time"
      actions={
        <SegmentedControl.Root
          size="1"
          value={bucket}
          onValueChange={(value) => setBucket(value as Bucket)}
        >
          {BUCKETS.map((name) => (
            <SegmentedControl.Item key={name} value={name}>
              {BUCKET_LABELS[name]}
            </SegmentedControl.Item>
          ))}
        </SegmentedControl.Root>
      }
    >
      {!series ? (
        <Flex justify="center" py="9">
          <Spinner size="3" />
        </Flex>
      ) : series.windows.length === 0 ? (
        <EmptyState icon={ChartColumnIcon} title="No records with a time" />
      ) : (
        <TimeBars
          valueLabel={series.unit}
          seriesLabel="Meter"
          bars={series.windows.map((window) => ({
            at: middle(window.start, window.end),
            value: window.quantity,
            series: window.objectId,
          }))}
        />
      )}
    </Section>
  );
}

/** The middle of a window, as a zone-less ISO timestamp (the chart shows it as given: UTC). */
function middle(start: string, end: string) {
  const ms = (parseUtc(start).getTime() + parseUtc(end).getTime()) / 2;
  return new Date(ms).toISOString().slice(0, 19);
}
