import { OcelTypeBadges } from "@ocelescope/core";
import {
  ArrowLeftRightIcon,
  BoxIcon,
  CalendarRangeIcon,
  CogIcon,
  DatabaseIcon,
  GaugeIcon,
  NetworkIcon,
} from "lucide-react";
import { AsyncBoundary, Section, StatCards, type StatItem } from "../../components";
import { useSelectedOcel } from "../../hooks/useSelectedOcel";
import { formatCount, formatDuration, formatPeriod, parseUtc } from "../../lib/format";
import { type SocelStatus, useSocelStatus } from "./useSocelStatus";

const toStats = (status: SocelStatus): StatItem[] => {
  const period =
    status.recordsFrom && status.recordsTo
      ? formatDuration(
          parseUtc(status.recordsTo).getTime() - parseUtc(status.recordsFrom).getTime(),
        )
      : undefined;

  return [
    {
      icon: BoxIcon,
      label: "Handling units",
      value: formatCount(status.handlingUnits),
      hint: `of ${formatCount(status.objects)} objects`,
    },
    {
      icon: CogIcon,
      label: "Operations",
      value: formatCount(status.operations),
      hint: `of ${formatCount(status.events)} events`,
    },
    { icon: GaugeIcon, label: "Flows", value: formatCount(status.flows) },
    {
      icon: NetworkIcon,
      label: "Flow instances",
      value: formatCount(status.flowInstances),
      hint: `${formatCount(status.containments)} contained`,
    },
    {
      icon: ArrowLeftRightIcon,
      label: "Flow records",
      value: formatCount(status.intervalRecords + status.eventRecords),
      hint: `${formatCount(status.intervalRecords)} interval · ${formatCount(status.eventRecords)} event`,
    },
    {
      icon: CalendarRangeIcon,
      label: "Recorded period",
      value: period ? `${period.value} ${period.unit}` : "–",
      hint:
        status.recordsFrom && status.recordsTo
          ? formatPeriod(status.recordsFrom, status.recordsTo)
          : undefined,
    },
  ];
};

// What the selected sOCEL holds: its name, what kind of log it is, and its counts.
export default function SocelSummary() {
  const status = useSocelStatus();
  const { name, extensions } = useSelectedOcel();

  return (
    <Section
      icon={DatabaseIcon}
      title={name ?? "sOCEL"}
      aside={<OcelTypeBadges extensions={extensions} />}
    >
      <AsyncBoundary
        status={status}
        loadingLabel="Reading the sOCEL…"
        errorTitle="The sOCEL could not be read"
        onRetry={() => void status.refetch()}
      >
        {(data) => <StatCards items={toStats(data)} />}
      </AsyncBoundary>
    </Section>
  );
}
