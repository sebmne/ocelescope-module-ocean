from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from socel import CheckResult, Finding

from ocelescope_module_socel.api_schema import ApiModel
from ocelescope_module_socel.overview.api.dependencies import get_validate_socel
from ocelescope_module_socel.overview.application.use_cases.validate_socel import (
    ValidateSocel,
    ValidateSocelCommand,
    ValidationResult,
)

router = APIRouter(tags=["sOCEL overview"])


class FindingModel(ApiModel):
    severity: Literal["error", "warning", "info"]
    message: str
    row_count: int

    @classmethod
    def from_domain(cls, finding: Finding) -> "FindingModel":
        return cls(
            severity=finding.severity.value,
            message=finding.message,
            row_count=finding.rows.height if finding.rows is not None else 0,
        )


class CheckResultModel(ApiModel):
    id: str
    title: str
    status: Literal["passed", "failed", "skipped"]
    reason: str | None
    findings: list[FindingModel]

    @classmethod
    def from_domain(cls, result: CheckResult) -> "CheckResultModel":
        return cls(
            id=result.check.id,
            title=result.check.title,
            status=result.status.value,
            reason=result.reason,
            findings=[FindingModel.from_domain(finding) for finding in result.findings],
        )


class ValidationResultModel(ApiModel):
    is_conforming: bool
    results: list[CheckResultModel]

    @classmethod
    def from_domain(cls, result: ValidationResult) -> "ValidationResultModel":
        return cls(
            is_conforming=result.report.is_conforming,
            results=[CheckResultModel.from_domain(r) for r in result.report.results],
        )


@router.post(
    "/{ocel_id}/validation",
    operation_id="validateSocel",
    responses={409: {"description": "The OCEL has no sOCEL tables."}},
)
def validate_socel(
    ocel_id: str, use_case: Annotated[ValidateSocel, Depends(get_validate_socel)]
) -> ValidationResultModel:
    """Checks the OCEL against the conformance rules V1–V9."""
    command = ValidateSocelCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = ValidationResultModel.from_domain(result)
    return response
