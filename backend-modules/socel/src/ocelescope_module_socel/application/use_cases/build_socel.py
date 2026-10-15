from dataclasses import dataclass

from ocelescope_module_socel.application.ports.socel_workspace import SocelWorkspace
from ocelescope_module_socel.application.workflows.apply_socel_changes import ApplySocelChanges
from ocelescope_module_socel.domain.models.preparation import PreparationDraft


@dataclass(frozen=True, kw_only=True)
class BuildSocelCommand:
    name: str
    preparation: PreparationDraft


class BuildSocel:
    def __init__(self, *, apply: ApplySocelChanges, workspace: SocelWorkspace) -> None:
        self._apply = apply
        self._workspace = workspace

    def execute(self, command: BuildSocelCommand) -> str:
        with self._workspace.open() as work:
            self._apply.apply(work, command.preparation)
            return work.publish_new(command.name)
