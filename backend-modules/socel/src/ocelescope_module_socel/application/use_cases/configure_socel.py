from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_workspace import SocelWorkspace
from ocelescope_module_socel.application.workflows.apply_socel_changes import ApplySocelChanges
from ocelescope_module_socel.domain.models.preparation import PreparationDraft


@dataclass(frozen=True, kw_only=True)
class ConfigureSocelCommand:
    preparation: PreparationDraft


class ConfigureSocel:
    """Apply changes to the bound original log, keeping its host identity."""

    def __init__(self, *, apply: ApplySocelChanges, workspace: SocelWorkspace) -> None:
        self._apply = apply
        self._workspace = workspace

    def execute(self, command: ConfigureSocelCommand) -> None:
        with self._workspace.open() as work:
            self._apply.apply(work, command.preparation)
            work.publish_replacing()
