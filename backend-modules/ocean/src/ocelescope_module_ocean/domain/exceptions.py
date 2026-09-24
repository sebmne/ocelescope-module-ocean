class OceanError(Exception):
    """Base class of all OCEAn domain errors; the API maps them to HTTP codes."""


class RuleProblem(OceanError):
    """Why a rule cannot be applied; turned into InvalidEmissionRuleError with its index."""


class InvalidEmissionRuleError(OceanError):
    """A rule cannot be applied to the OCEL, e.g. it uses an unknown activity."""

    def __init__(self, rule_index: int, message: str) -> None:
        super().__init__(f"Rule {rule_index + 1}: {message}")
        self.rule_index = rule_index


class EmissionsNotComputedError(OceanError):
    """A step needs emissions, but none were computed for the OCEL yet."""


class NoTargetObjectsError(OceanError):
    """The allocation has no target objects to allocate to."""


class AllocationIncompleteError(OceanError):
    """Emissions got lost during allocation; a bug, not a user error."""
