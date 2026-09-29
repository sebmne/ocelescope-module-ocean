from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.analysis.api.dependencies import (
    get_analysis_settings,
    get_save_analysis_settings,
)
from ocelescope_module_socel.analysis.application.use_cases.get_analysis_settings import (
    AnalysisSettingsView,
    GetAnalysisSettings,
    GetAnalysisSettingsCommand,
)
from ocelescope_module_socel.analysis.application.use_cases.save_analysis_settings import (
    SaveAnalysisSettings,
    SaveAnalysisSettingsCommand,
)
from ocelescope_module_socel.analysis.domain.models.analysis_settings import (
    AnalysisSettings,
    Choice,
    EmissionFactor,
)
from ocelescope_module_socel.api_schema import ApiModel

router = APIRouter(tags=["sOCEL analysis"])


class EmissionFactorModel(ApiModel):
    flow_id: str
    impact_per_unit: float

    def to_domain(self) -> EmissionFactor:
        return EmissionFactor(flow_id=self.flow_id, impact_per_unit=self.impact_per_unit)

    @classmethod
    def from_domain(cls, factor: EmissionFactor) -> "EmissionFactorModel":
        return cls(flow_id=factor.flow_id, impact_per_unit=factor.impact_per_unit)


class AnalysisSettingsModel(ApiModel):
    group_metering: bool = True
    created_from_qualifier: str | None = None
    mass_attribute: str | None = None
    emission_factors: list[EmissionFactorModel] = []

    def to_domain(self) -> AnalysisSettings:
        return AnalysisSettings(
            group_metering=self.group_metering,
            created_from_qualifier=self.created_from_qualifier,
            mass_attribute=self.mass_attribute,
            emission_factors=tuple(f.to_domain() for f in self.emission_factors),
        )

    @classmethod
    def from_domain(cls, settings: AnalysisSettings) -> "AnalysisSettingsModel":
        return cls(
            group_metering=settings.group_metering,
            created_from_qualifier=settings.created_from_qualifier,
            mass_attribute=settings.mass_attribute,
            emission_factors=[
                EmissionFactorModel.from_domain(f) for f in settings.emission_factors
            ],
        )


class ChoiceModel(ApiModel):
    name: str
    count: int

    @classmethod
    def from_domain(cls, choice: Choice) -> "ChoiceModel":
        return cls(name=choice.name, count=choice.count)


class AnalysisSettingsViewModel(ApiModel):
    settings: AnalysisSettingsModel
    created_from_qualifiers: list[ChoiceModel]
    mass_attributes: list[ChoiceModel]

    @classmethod
    def from_domain(cls, view: AnalysisSettingsView) -> "AnalysisSettingsViewModel":
        return cls(
            settings=AnalysisSettingsModel.from_domain(view.settings),
            created_from_qualifiers=[
                ChoiceModel.from_domain(c) for c in view.choices.created_from_qualifiers
            ],
            mass_attributes=[ChoiceModel.from_domain(c) for c in view.choices.mass_attributes],
        )


@router.get("/{ocel_id}/settings", operation_id="getAnalysisSettings")
def get_settings(
    ocel_id: str, use_case: Annotated[GetAnalysisSettings, Depends(get_analysis_settings)]
) -> AnalysisSettingsViewModel:
    """The OCEL's analysis settings, and the qualifiers and attributes it offers."""
    command = GetAnalysisSettingsCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = AnalysisSettingsViewModel.from_domain(result)
    return response


@router.put("/{ocel_id}/settings", operation_id="saveAnalysisSettings")
def save_settings(
    ocel_id: str,
    body: AnalysisSettingsModel,
    use_case: Annotated[SaveAnalysisSettings, Depends(get_save_analysis_settings)],
) -> AnalysisSettingsModel:
    """Replaces the OCEL's analysis settings."""
    command = SaveAnalysisSettingsCommand(ocel_id=ocel_id, settings=body.to_domain())
    result = use_case.execute(command)
    response = AnalysisSettingsModel.from_domain(result)
    return response
