from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from ocelescope_module_ocean.api.attribute_refs import (
    AttributeRefModel,
    attribute_ref_from_domain,
)
from ocelescope_module_ocean.api.dependencies import get_emission_rules, get_save_emission_rules
from ocelescope_module_ocean.api.schema import ApiModel
from ocelescope_module_ocean.application.use_cases.get_emission_rules import (
    GetEmissionRules,
    GetEmissionRulesCommand,
)
from ocelescope_module_ocean.application.use_cases.save_emission_rules import (
    SaveEmissionRules,
    SaveEmissionRulesCommand,
)
from ocelescope_module_ocean.domain.models.emission_rule_drafts import EmissionRuleDraft

router = APIRouter(tags=["Emission rules"])


# ---- Transport models: the rules as the editor holds them ----------------------


class RelationModel(ApiModel):
    """E2O rules only: the related objects that emit."""

    object_type: str
    qualifier: str | None = None


class FactorDraftModel(ApiModel):
    value: float | None = None
    attributes: list[AttributeRefModel] = []


class EmissionRuleDraftModel(ApiModel):
    id: str
    # The editor's names for the rule types.
    type: Literal["E", "E2O"]
    activity: str | None = None
    relation: RelationModel | None = None
    factor: FactorDraftModel

    def to_domain(self) -> EmissionRuleDraft:
        return EmissionRuleDraft(
            id=self.id,
            type="event" if self.type == "E" else "e2o",
            activity=self.activity,
            object_type=self.relation.object_type if self.relation else None,
            qualifier=self.relation.qualifier if self.relation else None,
            value_kg=self.factor.value,
            attributes=tuple(attribute.to_domain() for attribute in self.factor.attributes),
        )

    @classmethod
    def from_domain(cls, draft: EmissionRuleDraft) -> "EmissionRuleDraftModel":
        return cls(
            id=draft.id,
            type="E" if draft.type == "event" else "E2O",
            activity=draft.activity,
            relation=(
                RelationModel(object_type=draft.object_type, qualifier=draft.qualifier)
                if draft.object_type
                else None
            ),
            factor=FactorDraftModel(
                value=draft.value_kg,
                attributes=[attribute_ref_from_domain(a) for a in draft.attributes],
            ),
        )


class SaveEmissionRulesRequest(ApiModel):
    rules: list[EmissionRuleDraftModel]


# ---- Routes ------------------------------------------------------------------


@router.get("/{ocel_id}/emission-rules", operation_id="getEmissionRules")
def get_rules(
    ocel_id: str,
    use_case: Annotated[GetEmissionRules, Depends(get_emission_rules)],
) -> list[EmissionRuleDraftModel]:
    """The rules defined for an OCEL, complete or not; empty until some are saved."""
    command = GetEmissionRulesCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = [EmissionRuleDraftModel.from_domain(draft) for draft in result]
    return response


@router.put("/{ocel_id}/emission-rules", operation_id="saveEmissionRules")
def save_rules(
    ocel_id: str,
    body: SaveEmissionRulesRequest,
    use_case: Annotated[SaveEmissionRules, Depends(get_save_emission_rules)],
) -> list[EmissionRuleDraftModel]:
    """Replaces the rules defined for an OCEL."""
    command = SaveEmissionRulesCommand(
        ocel_id=ocel_id, drafts=tuple(rule.to_domain() for rule in body.rules)
    )
    result = use_case.execute(command)
    response = [EmissionRuleDraftModel.from_domain(draft) for draft in result]
    return response
