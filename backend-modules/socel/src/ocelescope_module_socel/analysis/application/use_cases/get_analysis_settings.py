from dataclasses import dataclass

from ocelescope import OCEL
from socel import SOCEL, unit_attributes, unit_relation_qualifiers

from ocelescope_module_socel.analysis.application.ports.settings_repository import (
    SettingsRepository,
)
from ocelescope_module_socel.analysis.domain.models.analysis_settings import (
    AnalysisSettings,
    Choice,
    SettingsChoices,
)


@dataclass(frozen=True, kw_only=True)
class GetAnalysisSettingsCommand:
    ocel_id: str


@dataclass(frozen=True, kw_only=True)
class AnalysisSettingsView:
    settings: AnalysisSettings
    choices: SettingsChoices


class GetAnalysisSettings:
    """The OCEL's analysis settings (defaults until saved), and what it offers for them."""

    def __init__(self, *, ocel: OCEL, settings: SettingsRepository) -> None:
        self._ocel = ocel
        self._settings = settings

    def execute(self, command: GetAnalysisSettingsCommand) -> AnalysisSettingsView:
        socel = SOCEL(self._ocel)
        return AnalysisSettingsView(
            settings=self._settings.get(command.ocel_id),
            choices=SettingsChoices(
                created_from_qualifiers=tuple(
                    Choice(name=name, count=count)
                    for name, count in unit_relation_qualifiers(socel).iter_rows()
                ),
                mass_attributes=tuple(
                    Choice(name=name, count=count)
                    for name, count in unit_attributes(socel).iter_rows()
                ),
            ),
        )
