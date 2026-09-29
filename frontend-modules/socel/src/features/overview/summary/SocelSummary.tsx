import {
  ArrowLeftRightIcon,
  BoxIcon,
  CalendarRangeIcon,
  CogIcon,
  DatabaseIcon,
  DownloadIcon,
  GaugeIcon,
  NetworkIcon,
} from "lucide-react";
import { useExportSocel } from "../../../data/overview/useExportSocel";
import { useSocelStatus } from "../../../data/overview/useSocelStatus";
import { formatCount, formatDuration, formatPeriod, parseUtc } from "../../../lib/format";
import { Button, EmptyState, Flex, Grid, Notice, Section, Spinner, Stat } from "../../../ui";

// What the selected sOCEL holds, and its download as SQLite.
export default function SocelSummary() {
  const status = useSocelStatus().data;
  const { download, isPending, error } = useExportSocel();

  if (!status) {
    return (
      <Flex justify="center" py="9">
        <Spinner size="3" />
      </Flex>
    );
  }

  if (!status.isSocel) {
    return <EmptyState icon={DatabaseIcon} title={`${status.ocelName} is no sOCEL`} />;
  }

  const period =
    status.recordsFrom && status.recordsTo
      ? {
          ...formatDuration(
            parseUtc(status.recordsTo).getTime() - parseUtc(status.recordsFrom).getTime(),
          ),
          hint: formatPeriod(status.recordsFrom, status.recordsTo),
        }
      : undefined;

  return (
    <Section
      icon={DatabaseIcon}
      title={status.ocelName}
      actions={
        <Button
          variant="soft"
          loading={isPending}
          onClick={() => download(`${status.ocelName}.sqlite`)}
        >
          <DownloadIcon size={15} aria-hidden /> SQLite
        </Button>
      }
    >
      <Grid columns={{ initial: "2", md: "3" }} gap={{ initial: "3", md: "4" }}>
        <Stat
          icon={BoxIcon}
          label="Handling units"
          value={formatCount(status.handlingUnits)}
          hint={`of ${formatCount(status.objects)} objects`}
        />
        <Stat
          icon={CogIcon}
          label="Operations"
          value={formatCount(status.operations)}
          hint={`of ${formatCount(status.events)} events`}
        />
        <Stat icon={GaugeIcon} label="Flows" value={formatCount(status.flows)} />
        <Stat
          icon={NetworkIcon}
          label="Flow instances"
          value={formatCount(status.flowInstances)}
          hint={`${formatCount(status.containments)} contained`}
        />
        <Stat
          icon={ArrowLeftRightIcon}
          label="Flow records"
          value={formatCount(status.intervalRecords + status.eventRecords)}
          hint={`${formatCount(status.intervalRecords)} interval · ${formatCount(status.eventRecords)} event`}
        />
        <Stat icon={CalendarRangeIcon} label="Recorded period" {...(period ?? { value: "–" })} />
      </Grid>
      {error && <Notice tone="error">{error}</Notice>}
    </Section>
  );
}
