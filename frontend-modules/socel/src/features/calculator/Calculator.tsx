import { CalculatorIcon, CloudIcon, GaugeIcon } from "lucide-react";
import { useState } from "react";
import { AsyncBoundary, Section, SegmentedControl, StatCards } from "../../components";
import { formatAmount, formatCount } from "../../lib/format";
import FactorTable from "./FactorTable";
import ImpactChart from "./ImpactChart";
import { usableFactors } from "./impact";
import { useFactors } from "./useFactors";
import { type Period, useImpact } from "./useImpact";

const PERIODS: { value: Period; label: string }[] = [
  { value: "hour", label: "Hour" },
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
];

// The impact of the sOCEL's flows in kg CO2e, from a factor per flow (thesis,
// Def. 6.4.1): the total, its course over time, and the factors.
export default function Calculator() {
  const [period, setPeriod] = useState<Period>("day");
  const { factors, change } = useFactors();
  const impact = useImpact(period, usableFactors(factors));

  return (
    <AsyncBoundary
      status={impact}
      loadingLabel="Summing the flows…"
      errorTitle="The flows could not be summed"
      onRetry={() => void impact.refetch()}
    >
      {({ flows, total, byPeriod }) => {
        const withFactor = flows.filter((flow) => flow.impact !== null).length;
        return (
          <>
            <Section
              icon={CloudIcon}
              title="Impact"
              aside={
                <SegmentedControl.Root
                  size="1"
                  ml="auto"
                  value={period}
                  onValueChange={(value) => setPeriod(value as Period)}
                >
                  {PERIODS.map(({ value, label }) => (
                    <SegmentedControl.Item key={value} value={value}>
                      {label}
                    </SegmentedControl.Item>
                  ))}
                </SegmentedControl.Root>
              }
            >
              <StatCards
                items={[
                  { icon: CloudIcon, label: "kg CO₂e", value: formatAmount(total) },
                  {
                    icon: GaugeIcon,
                    label: "Flows with a factor",
                    value: formatCount(withFactor),
                    hint: `of ${formatCount(flows.length)}`,
                  },
                ]}
              />
              <ImpactChart rows={byPeriod} />
            </Section>
            <Section icon={CalculatorIcon} title="Factors">
              <FactorTable rows={flows} total={total} factors={factors} onChange={change} />
            </Section>
          </>
        );
      }}
    </AsyncBoundary>
  );
}
