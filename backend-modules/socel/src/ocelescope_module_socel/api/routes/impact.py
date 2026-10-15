from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_calculate_impact
from ocelescope_module_socel.application.use_cases.calculate_impact import (
    CalculateImpact,
    CalculateImpactCommand,
)
from ocelescope_module_socel.domain.models.impact_analysis import ImpactAnalysis, ImpactReport

router = APIRouter()


@router.post(
    "/impact",
    operation_id="calculateImpact",
    responses={422: {"description": "The OCEL is no sOCEL, or a factor is no finite number."}},
)
def calculate_impact(
    analysis: ImpactAnalysis,
    use_case: Annotated[CalculateImpact, Depends(get_calculate_impact)],
) -> ImpactReport:
    """Calculate impact in kg CO2e, per flow and period, without storing it.

    Each direction has its own factor on its nonnegative amount. Records are
    counted by their share of each period; records covered by a containing
    instance's records are excluded.
    """
    return use_case.execute(CalculateImpactCommand(analysis=analysis))
