from ocelescope import OCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.use_cases.socel_changes import (
    ApplySocelChanges,
    SocelChanges,
)


class BuildSocelCommand(Command):
    ocel: OCEL
    """The name the new log is kept under."""
    name: str
    changes: SocelChanges


class BuildSocel:
    """Turns a log into an sOCEL kept as a new log, beside the one it came from.
    Returns the new log's id."""

    def __init__(self, *, apply: ApplySocelChanges, store: LogStore) -> None:
        self._apply = apply
        self._store = store

    def execute(self, command: BuildSocelCommand) -> str:
        with self._apply(command.ocel, command.changes) as built:
            return self._store.add(built, command.name)
