import unittest

from test_validation import add_extension_tables, make_ocel

from socel import (
    DEFAULT_TAXONOMY,
    SOCEL,
    ClassDomain,
    FlowDirection,
    Node,
    SOCELValidationError,
    Taxonomy,
)


class TaxonomyTests(unittest.TestCase):
    def test_taxonomies_keep_flow_categories_and_classes_separate(self) -> None:
        taxonomies = DEFAULT_TAXONOMY

        self.assertIsNotNone(taxonomies.flow_categories.resolve("energy.electricity"))
        self.assertIsNone(taxonomies.object_classes.resolve("energy.electricity"))
        self.assertIsNotNone(
            taxonomies.object_classes.resolve("pr.processing.mechanical")
        )
        self.assertIsNotNone(
            taxonomies.event_classes.resolve("op.manufacturing.forming")
        )

    def test_taxonomy_supports_tree_navigation(self) -> None:
        categories = DEFAULT_TAXONOMY.flow_categories

        self.assertTrue(categories.is_a("material.auxiliary.gas", "material"))
        self.assertEqual(
            categories.ancestors("material.auxiliary.gas"),
            ["material.auxiliary", "material"],
        )
        self.assertIn(
            "material.auxiliary.gas",
            categories.descendants("material"),
        )

    def test_tree_names_are_not_part_of_encoded_paths(self) -> None:
        categories = DEFAULT_TAXONOMY.flow_categories

        self.assertIsNone(categories.resolve("technosphere"))
        self.assertEqual(categories.tree_name("energy.electricity"), "technosphere")
        self.assertEqual(categories.tree_name("emission"), "elementary")

    def test_paths_are_derived_from_local_node_values(self) -> None:
        taxonomy = Taxonomy({"example": [Node("root", [Node("child")])]})

        self.assertEqual(list(taxonomy), ["root", "root.child"])
        child = taxonomy.require("root.child")
        self.assertEqual(child.value, "child")

    def test_signatures_inherit_from_parent_classes(self) -> None:
        signature = DEFAULT_TAXONOMY.signatures.for_event_class(
            "op.manufacturing.separating"
        )

        self.assertIsNotNone(signature)
        assert signature is not None
        self.assertEqual(signature.domain, ClassDomain.EVENT)
        expected = {
            (entry.category_id, entry.direction) for entry in signature.expected_flows
        }
        self.assertIn(("energy", FlowDirection.INPUT), expected)
        self.assertIn(("material.auxiliary", FlowDirection.INPUT), expected)
        self.assertIn(("material.workpiece", FlowDirection.OUTPUT), expected)

    def test_signatures_represent_alternatives_and_conditions(self) -> None:
        signature = DEFAULT_TAXONOMY.signatures.for_object_class(
            "pr.processing.thermal"
        )

        self.assertIsNotNone(signature)
        assert signature is not None
        alternatives = {
            entry.category_id
            for entry in signature.expected_flows
            if entry.alternative_group == "energy-source"
        }
        self.assertEqual(alternatives, {"energy.fuel", "energy.electricity"})
        emission = next(
            entry
            for entry in signature.expected_flows
            if entry.category_id == "emission"
        )
        self.assertEqual(emission.condition_category_id, "energy.fuel")

    def test_unknown_custom_categories_are_rejected(self) -> None:
        ocel = make_ocel()
        try:
            add_extension_tables(ocel)
            ocel.con.execute(
                "INSERT INTO socel_flow VALUES "
                "('custom-flow', 'widgets', 'company.custom', NULL)"
            )

            with self.assertRaisesRegex(
                SOCELValidationError, r"\[V10\].*company.custom"
            ):
                SOCEL.from_ocel(ocel)
        finally:
            ocel.close()


if __name__ == "__main__":
    unittest.main()
