from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.use_cases.socel_changes import (
    ApplySocelChanges,
    SocelChanges,
)


class ConfigureSocelCommand(Command):
    ocel_id: str
    changes: SocelChanges


class ConfigureSocel:
    """Changes an sOCEL in place: classes, and flows with their records. The
    whole log is changed, not the part the app's filters show, and it keeps its
    id and name."""

    def __init__(self, *, apply: ApplySocelChanges, store: LogStore) -> None:
        self._apply = apply
        self._store = store

    def execute(self, command: ConfigureSocelCommand) -> None:
        with (
            self._store.get(command.ocel_id) as ocel,
            self._apply(ocel, command.changes) as changed,
        ):
            self._store.replace(command.ocel_id, changed)
