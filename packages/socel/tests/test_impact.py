import unittest
from math import inf

from socel.analysis import (
    AllocatedImpactResult,
    AllocationResult,
    CarriedQuantityResult,
    EventImpact,
    EventImpactResult,
    FlowAllocation,
    FlowCarriedQuantity,
    FlowEventQuantity,
    HandlingUnitImpact,
    HandlingUnitQuantity,
    ImpactFactors,
    ProductFootprintResult,
    impact_allocations,
    impact_events,
    impact_quantity,
    product_footprints,
)


class ImpactFactorTests(unittest.TestCase):
    def test_factors_reject_empty_flow_identifiers(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            ImpactFactors({"": 1.0})

    def test_factors_reject_non_numeric_and_non_finite_values(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be numeric"):
            ImpactFactors({"electricity": True})
        with self.assertRaisesRegex(ValueError, "must be finite"):
            ImpactFactors({"electricity": inf})

    def test_factors_are_copied_and_immutable(self) -> None:
        source = {"electricity": 0.5}
        factors = ImpactFactors(source)

        source["electricity"] = 2.0

        self.assertEqual(factors.for_flow("electricity"), 0.5)
        with self.assertRaises(TypeError):
            factors.values["electricity"] = 3.0  # type: ignore[index]

    def test_missing_factor_has_a_domain_error(self) -> None:
        factors = ImpactFactors({"electricity": 0.5})

        with self.assertRaisesRegex(ValueError, "Missing impact factor.*gas"):
            factors.for_flow("gas")


class ImpactResultTests(unittest.TestCase):
    def test_results_reject_duplicate_elements(self) -> None:
        with self.assertRaisesRegex(ValueError, "each event once"):
            EventImpactResult((EventImpact("event-1", 1.0),) * 2)
        duplicate_handling_units = (HandlingUnitImpact("product-1", 1.0),) * 2
        with self.assertRaisesRegex(ValueError, "each handling unit once"):
            AllocatedImpactResult(duplicate_handling_units, 0.0)
        with self.assertRaisesRegex(ValueError, "each handling unit once"):
            ProductFootprintResult(duplicate_handling_units, 0.0)


class ImpactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factors = ImpactFactors({"electricity": 0.5, "gas": 3.0})

    def test_impact_quantity_multiplies_by_the_flow_factor(self) -> None:
        self.assertEqual(impact_quantity("electricity", 8.0, self.factors), 4.0)

    def test_event_impacts_sum_converted_quantities_across_flows(self) -> None:
        result = impact_events(
            (
                FlowEventQuantity("electricity", "event-1", 10.0),
                FlowEventQuantity("gas", "event-1", 2.0),
                FlowEventQuantity("electricity", "event-2", 4.0),
            ),
            self.factors,
        )

        self.assertEqual(result.for_event("event-1"), 11.0)
        self.assertEqual(result.for_event("event-2"), 2.0)
        self.assertEqual(result.total, 13.0)

    def test_allocated_impacts_include_the_converted_remainder(self) -> None:
        allocation = AllocationResult(
            (
                FlowAllocation(
                    flow_id="electricity",
                    handling_units=(
                        HandlingUnitQuantity("product-1", 10.0),
                        HandlingUnitQuantity("product-2", 5.0),
                    ),
                    unallocated=2.0,
                    recorded=17.0,
                ),
                FlowAllocation(
                    flow_id="gas",
                    handling_units=(HandlingUnitQuantity("product-1", 2.0),),
                    unallocated=1.0,
                    recorded=3.0,
                ),
            )
        )

        result = impact_allocations(allocation, self.factors)

        self.assertEqual(result.for_handling_unit("product-1"), 11.0)
        self.assertEqual(result.for_handling_unit("product-2"), 2.5)
        self.assertEqual(result.allocated, 13.5)
        self.assertEqual(result.unallocated, 4.0)

    def test_product_footprints_sum_converted_carried_quantities(self) -> None:
        carried = CarriedQuantityResult(
            (
                FlowCarriedQuantity(
                    flow_id="electricity",
                    handling_units=(HandlingUnitQuantity("product-1", 12.0),),
                    unallocated=2.0,
                ),
                FlowCarriedQuantity(
                    flow_id="gas",
                    handling_units=(HandlingUnitQuantity("product-1", 3.0),),
                    unallocated=1.0,
                ),
            )
        )

        result = product_footprints(carried, self.factors)

        self.assertEqual(result.for_handling_unit("product-1"), 15.0)
        self.assertEqual(result.unallocated, 4.0)


if __name__ == "__main__":
    unittest.main()
