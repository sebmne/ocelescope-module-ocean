import { BoxIcon, CogIcon } from "lucide-react";
import { useMemo } from "react";
import { AsyncBoundary, Grid } from "../../components";
import type { Changes } from "../../hooks/useBuildSocel";
import { useClassTaxonomies } from "../../hooks/useClassTaxonomies";
import { type TypeClassification, useLogClassification } from "../../hooks/useLogClassification";
import { classOptions } from "../../lib/classOptions";
import TypeCard from "./TypeCard";

const classOfIn =
  (types: readonly TypeClassification[], changes: Changes) =>
  (name: string): string | null =>
    name in changes
      ? changes[name]
      : (types.find((type) => type.name === name)?.socelClass ?? null);

interface ClassificationProps {
  /** The classes set here, per activity and per object type; the rest keep theirs. */
  activities: Changes;
  objectTypes: Changes;
  onActivities: (changes: Changes) => void;
  onObjectTypes: (changes: Changes) => void;
}

// The activities and the object types of the selected log, each with the class
// of the taxonomy it has or is given here.
export default function Classification({
  activities,
  objectTypes,
  onActivities,
  onObjectTypes,
}: ClassificationProps) {
  const classification = useLogClassification();
  const taxonomies = useClassTaxonomies();
  const eventClasses = useMemo(
    () => classOptions(taxonomies.data?.eventClasses ?? []),
    [taxonomies.data],
  );
  const objectClasses = useMemo(
    () => classOptions(taxonomies.data?.objectClasses ?? []),
    [taxonomies.data],
  );

  return (
    <AsyncBoundary
      status={classification}
      loadingLabel="Reading the log…"
      errorTitle="The log could not be read"
      onRetry={() => void classification.refetch()}
    >
      {(data) => (
        <Grid columns={{ initial: "1", lg: "2" }} gap="4" align="start">
          <TypeCard
            icon={CogIcon}
            title="Activities"
            colorScope="activity"
            types={data.activities}
            options={eventClasses}
            classOf={classOfIn(data.activities, activities)}
            onChange={(type, socelClass) => onActivities({ ...activities, [type]: socelClass })}
          />
          <TypeCard
            icon={BoxIcon}
            title="Object types"
            colorScope="objectType"
            types={data.objectTypes}
            options={objectClasses}
            classOf={classOfIn(data.objectTypes, objectTypes)}
            onChange={(type, socelClass) => onObjectTypes({ ...objectTypes, [type]: socelClass })}
          />
        </Grid>
      )}
    </AsyncBoundary>
  );
}
