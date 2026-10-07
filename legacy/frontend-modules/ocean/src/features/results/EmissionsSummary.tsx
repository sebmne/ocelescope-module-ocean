import { BoxIcon, CloudIcon, FileInputIcon, ListChecksIcon } from "lucide-react";
import { useEmissionsOverview } from "../../data/useEmissionsOverview";
import { useObjectEmissions } from "../../data/useObjectEmissions";
import { formatCount, formatExactKg, formatShare, massParts } from "../../lib/format";
import { Grid, Stat } from "../../ui";

// The key figures, always in view at the top: how much, from where, and per object.
export default function EmissionsSummary() {
  const overview = useEmissionsOverview().data;
  const allocation = useObjectEmissions().data;

  const total = massParts(overview?.totalKg);
  const ruleBased = massParts(overview?.ruleBasedKg);
  const imported = massParts(overview?.importedKg);
  const perObject = massParts(
    allocation && allocation.targetObjects > 0
      ? allocation.totalKg / allocation.targetObjects
      : null,
  );

  return (
    <Grid columns={{ initial: "2", md: "4" }} gap={{ initial: "3", md: "4" }}>
      <Stat
        highlight
        icon={CloudIcon}
        label="Total emissions"
        value={total.value}
        unit={total.unit && `${total.unit} CO₂e`}
        hint={overview?.totalKg == null ? undefined : formatExactKg(overview.totalKg)}
      />
      <Stat
        icon={ListChecksIcon}
        label="From rules"
        value={ruleBased.value}
        unit={ruleBased.unit}
        hint={formatShare(overview?.ruleBasedKg, overview?.totalKg)}
      />
      <Stat
        icon={FileInputIcon}
        label="Imported"
        value={imported.value}
        unit={imported.unit}
        hint={formatShare(overview?.importedKg, overview?.totalKg)}
      />
      <Stat
        icon={BoxIcon}
        label="Per target object"
        value={perObject.value}
        unit={perObject.unit}
        hint={allocation ? `⌀ over ${formatCount(allocation.targetObjects)} objects` : undefined}
      />
    </Grid>
  );
}
