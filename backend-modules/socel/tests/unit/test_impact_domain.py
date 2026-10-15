"""Business examples that can run without the HTTP/host fixtures.

Run with --confcutdir=tests/unit to exercise only the domain and use case.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from ocelescope_module_socel.application.use_cases.calculate_impact import (
    CalculateImpact,
    CalculateImpactCommand,
)
from ocelescope_module_socel.domain.models.flow_quantities import (
    FlowQuantity,
    Period,
    PeriodQuantity,
)
from ocelescope_module_socel.domain.models.impact_analysis import DirectionFactors, ImpactAnalysis
from ocelescope_module_socel.domain.services.impact_calculator import ImpactCalculator


@pytest.mark.parametrize(
    ("factors", "expected"),
    [
        (DirectionFactors(), None),
        (DirectionFactors(inflow=0), 0),
        (DirectionFactors(outflow=0), 0),
        (DirectionFactors(inflow=0.5, outflow=3), 11),
        (DirectionFactors(outflow=-2), -4),
    ],
)
def test_factors_own_directional_application(
    factors: DirectionFactors, expected: float | None
) -> None:
    assert factors.apply(inflow=10, outflow=2) == expected


@pytest.mark.parametrize("field", ["inflow", "outflow"])
@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_factors_are_invalid_outside_http(field: str, value: float) -> None:
    with pytest.raises(ValidationError, match="finite"):
        DirectionFactors.model_validate({field: value})


@pytest.mark.parametrize("field", ["inflow", "outflow"])
@pytest.mark.parametrize("value", [-1, float("inf"), float("nan")])
def test_directional_amounts_are_finite_and_nonnegative(field: str, value: float) -> None:
    data = {"start": datetime(2026, 1, 1), "inflow": 0, "outflow": 0, field: value}
    with pytest.raises(ValidationError):
        PeriodQuantity.model_validate(data)
    with pytest.raises(ValidationError):
        FlowQuantity.model_validate({"flowId": "heat", "unit": "kWh", "byPeriod": [], **data})


@pytest.fixture
def quantities() -> tuple[FlowQuantity, ...]:
    return (
        FlowQuantity(
            flow_id="heat",
            unit="kWh",
            inflow=0,
            outflow=4,
            by_period=(PeriodQuantity(start=datetime(2026, 1, 1), inflow=0, outflow=4),),
        ),
        FlowQuantity(
            flow_id="electricity",
            unit="kWh",
            inflow=10,
            outflow=2,
            by_period=(
                PeriodQuantity(start=datetime(2026, 1, 2), inflow=6, outflow=2),
                PeriodQuantity(start=datetime(2026, 1, 1), inflow=4, outflow=0),
            ),
        ),
    )


def test_calculator_combines_flows_and_orders_periods(quantities: tuple[FlowQuantity, ...]) -> None:
    analysis = ImpactAnalysis(
        factors={
            "heat": DirectionFactors(outflow=2),
            "electricity": DirectionFactors(inflow=0.5, outflow=3),
            "absent": DirectionFactors(inflow=100),
        }
    )
    report = ImpactCalculator().calculate(quantities, analysis)

    assert [(flow.flow_id, flow.impact) for flow in report.flows] == [
        ("heat", 8),
        ("electricity", 11),
    ]
    assert report.total == 19
    assert [(part.start.day, part.flow_id, part.impact) for part in report.by_period] == [
        (1, "electricity", 2),
        (1, "heat", 8),
        (2, "electricity", 9),
    ]


def test_absent_factors_stay_distinct_from_zero(quantities: tuple[FlowQuantity, ...]) -> None:
    report = ImpactCalculator().calculate(
        quantities, ImpactAnalysis(factors={"electricity": DirectionFactors(inflow=0)})
    )

    assert [flow.impact for flow in report.flows] == [None, 0]
    assert report.total == 0
    assert [(part.flow_id, part.impact) for part in report.by_period] == [
        ("electricity", 0),
        ("electricity", 0),
    ]


def test_empty_analysis_has_zero_impact() -> None:
    report = ImpactCalculator().calculate((), ImpactAnalysis(factors={}))
    assert report.total == 0
    assert report.flows == ()
    assert report.by_period == ()


def test_use_case_reads_the_requested_period(quantities: tuple[FlowQuantity, ...]) -> None:
    class FlowReader:
        def __init__(self) -> None:
            self.period: Period | None = None

        def quantities(self, period: Period) -> tuple[FlowQuantity, ...]:
            self.period = period
            return quantities

    reader = FlowReader()
    use_case = CalculateImpact(flows=reader, calculator=ImpactCalculator())
    report = use_case.execute(
        CalculateImpactCommand(
            analysis=ImpactAnalysis(period="week", factors={"heat": DirectionFactors(outflow=2)})
        )
    )

    assert reader.period == "week"
    assert report.total == 8
