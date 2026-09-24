from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import Field

from ocelescope_module_ocean.api.dependencies import get_compute_emissions, get_emissions_overview
from ocelescope_module_ocean.api.schema import ApiModel
from ocelescope_module_ocean.application.use_cases.compute_emissions import (
    ComputeEmissions,
    ComputeEmissionsCommand,
)
from ocelescope_module_ocean.application.use_cases.get_emissions_overview import (
    GetEmissionsOverview,
    GetEmissionsOverviewCommand,
)
from ocelescope_module_ocean.domain.models.attributes import EventAttribute, ObjectAttribute
from ocelescope_module_ocean.domain.models.emission_factor import EmissionFactor
from ocelescope_module_ocean.domain.models.emission_rules import E2OEmissionRule, EventEmissionRule
from ocelescope_module_ocean.domain.models.emissions import EmissionsOverview

router = APIRouter(tags=["Emissions"])


# ---- Request models ----------------------------------------------------------


class EventAttributeRef(ApiModel):
    target: Literal["event"]
    name: str

    def to_domain(self) -> EventAttribute:
        return EventAttribute(name=self.name)


class ObjectAttributeRef(ApiModel):
    target: Literal["object"]
    object_type: str
    name: str
    qualifier: str | None = None

    def to_domain(self) -> ObjectAttribute:
        return ObjectAttribute(
            object_type=self.object_type, name=self.name, qualifier=self.qualifier
        )


class EmissionFactorRequest(ApiModel):
    value_kg: float
    attributes: list[
        Annotated[EventAttributeRef | ObjectAttributeRef, Field(discriminator="target")]
    ] = []

    def to_domain(self) -> EmissionFactor:
        return EmissionFactor(
            value_kg=self.value_kg,
            attributes=tuple(attribute.to_domain() for attribute in self.attributes),
        )


class EventEmissionRuleRequest(ApiModel):
    type: Literal["E"]
    activity: str
    factor: EmissionFactorRequest

    def to_domain(self) -> EventEmissionRule:
        return EventEmissionRule(activity=self.activity, factor=self.factor.to_domain())


class E2OEmissionRuleRequest(ApiModel):
    type: Literal["E2O"]
    activity: str
    object_type: str
    qualifier: str | None = None
    factor: EmissionFactorRequest

    def to_domain(self) -> E2OEmissionRule:
        return E2OEmissionRule(
            activity=self.activity,
            object_type=self.object_type,
            qualifier=self.qualifier,
            factor=self.factor.to_domain(),
        )


class ComputeEmissionsRequest(ApiModel):
    rules: list[
        Annotated[EventEmissionRuleRequest | E2OEmissionRuleRequest, Field(discriminator="type")]
    ]


# ---- Response models ---------------------------------------------------------


class EmissionsOverviewResponse(ApiModel):
    rule_based_kg: float | None
    imported_kg: float | None
    total_kg: float | None

    @classmethod
    def from_domain(cls, overview: EmissionsOverview) -> "EmissionsOverviewResponse":
        return cls(
            rule_based_kg=overview.rule_based_kg,
            imported_kg=overview.imported_kg,
            total_kg=overview.total_kg,
        )


# ---- Routes ------------------------------------------------------------------


@router.get("/{ocel_id}/emissions/overview", operation_id="getEmissionsOverview")
def get_overview(
    ocel_id: str,
    use_case: Annotated[GetEmissionsOverview, Depends(get_emissions_overview)],
) -> EmissionsOverviewResponse:
    """Totals of the emissions computed for an OCEL; null until emissions are computed."""
    command = GetEmissionsOverviewCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = EmissionsOverviewResponse.from_domain(result)
    return response


@router.post(
    "/{ocel_id}/emissions",
    operation_id="computeEmissions",
    responses={422: {"description": "A rule does not fit the OCEL."}},
)
def compute_emissions(
    ocel_id: str,
    body: ComputeEmissionsRequest,
    use_case: Annotated[ComputeEmissions, Depends(get_compute_emissions)],
) -> EmissionsOverviewResponse:
    """Applies the emission rules to the OCEL and returns the new totals."""
    command = ComputeEmissionsCommand(
        ocel_id=ocel_id, rules=tuple(rule.to_domain() for rule in body.rules)
    )
    result = use_case.execute(command)
    response = EmissionsOverviewResponse.from_domain(result)
    return response
