import { ShieldCheckIcon } from "lucide-react";
import { useSocelStatus } from "../../../data/overview/useSocelStatus";
import { useLastValidation, useValidateSocel } from "../../../data/overview/useValidateSocel";
import { Button, EmptyState, Notice, Section, type Status } from "../../../ui";
import ValidationReport from "./ValidationReport";

// Checks the selected sOCEL against the thesis' rules V1–V9. Only shown for an sOCEL.
export default function ValidationSection() {
  const isSocel = useSocelStatus().data?.isSocel ?? false;
  const { validate, isPending, error } = useValidateSocel();
  const last = useLastValidation();

  if (!isSocel) return null;

  const status: Status = isPending
    ? { tone: "busy", label: "Validating" }
    : !last
      ? { tone: "idle", label: "Not validated" }
      : last.isConforming
        ? { tone: "done", label: "Conforming" }
        : { tone: "attention", label: "Not conforming" };

  const button = (
    <Button onClick={validate} loading={isPending} variant={last ? "soft" : "solid"}>
      <ShieldCheckIcon size={15} aria-hidden /> {last ? "Validate again" : "Validate"}
    </Button>
  );

  return (
    <Section icon={ShieldCheckIcon} title="Validation" status={status} actions={last && button}>
      {last ? (
        <ValidationReport result={last} />
      ) : (
        <EmptyState icon={ShieldCheckIcon} title="V1–V9" action={button} />
      )}
      {error && <Notice tone="error">{error}</Notice>}
    </Section>
  );
}
