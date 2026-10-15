"""Retained validation semantics beyond the host's one-rule recognition cases."""

from copy import deepcopy

import pytest
from ocelescope import OCELExtensionError
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.application.use_cases.get_class_taxonomies import (
    GetClassTaxonomies,
    GetClassTaxonomiesCommand,
)
from ocelescope_module_socel.domain.models.preparation import PreparationDraft, PreparationFacts
from ocelescope_module_socel.domain.models.record_file import FlowDefinition
from ocelescope_module_socel.domain.services.preparation_validator import PreparationValidator
from ocelescope_module_socel.domain.taxonomies import TAXONOMY
from ocelescope_module_socel.infrastructure.conformance import SocelValidationError
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL


def test_missing_structure_reports_all_tables_and_skips_dependent_queries(
    session: Session, plain_log: str
) -> None:
    with session.get_ocel(plain_log) as source:
        with pytest.raises(OCELExtensionError) as raised:
            SOCEL.from_ocel(source)
        cause = raised.value.__cause__
        assert isinstance(cause, SocelValidationError)
        assert len(cause.issues) == 4
        assert {issue.rule for issue in cause.issues} == {"V1"}
        for table in (
            "socel_flow",
            "socel_interval_records",
            "socel_event_records",
            "socel_containedin",
        ):
            assert any(table in message for message in cause.messages)
        assert source.sql("SELECT 1").fetchone() == (1,)


def test_independent_issues_accumulate_and_failed_prerequisites_skip_overlap_checks(
    session: Session, socel: str
) -> None:
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.sql("""
            INSERT INTO socel_interval_records
            SELECT 'overlapping', flow_id, object_id, quantity, start_time, end_time
            FROM socel_interval_records WHERE object_id = 'm1';
            UPDATE socel_interval_records SET end_time = start_time WHERE object_id = 'm2';
            UPDATE socel_event_records SET record_id = 'overlapping';
        """)
        with SOCEL(changed.con.cursor()) as extension:
            with pytest.raises(SocelValidationError) as raised:
                extension.validate()
        assert {issue.rule for issue in raised.value.issues} == {"V3", "V4"}


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        ("UPDATE socel_interval_records SET quantity = NULL", "null value"),
        ("INSERT INTO socel_flow SELECT * FROM socel_flow WHERE flow_id = 'heat'", "primary-key"),
        ("ALTER TABLE socel_flow DROP COLUMN unit", "socel_flow.unit is missing"),
        (
            "ALTER TABLE socel_interval_records ALTER start_time TYPE VARCHAR",
            "expected timestamp",
        ),
    ],
)
def test_storage_structure_checks_remain_strict(
    session: Session, socel: str, mutation: str, detail: str
) -> None:
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.sql(mutation)
        with SOCEL(changed.con.cursor()) as extension:
            with pytest.raises(SocelValidationError) as raised:
                extension.validate()
        assert {issue.rule for issue in raised.value.issues} == {"V1"}
        assert detail in str(raised.value)


def test_taxonomy_diagnostics_include_all_assigned_concepts(session: Session, socel: str) -> None:
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.sql("""
            UPDATE socel_flow SET category = NULL WHERE flow_id = 'heat';
            UPDATE socel_flow SET category = 'custom.energy' WHERE flow_id = 'electricity';
            UPDATE events SET socel_class = 'op.custom' WHERE "ocel:eid" = 'e1';
            UPDATE object_changes SET socel_class = 'pr.custom'
                WHERE "ocel:oid" = 'm1' AND "ocel:field" = 'socel_class';
        """)
        with SOCEL(changed.con.cursor()) as extension:
            with pytest.raises(SocelValidationError) as raised:
                extension.validate()
        assert len(raised.value.issues) == 4
        assert {issue.rule for issue in raised.value.issues} == {"V10"}
        assert all(value in str(raised.value) for value in ("heat", "custom.energy", "e1", "m1"))


@pytest.mark.parametrize("category", ["energy", "material.auxiliary", "material.auxiliary.gas"])
def test_preparation_api_choices_and_conformance_use_the_fixed_taxonomy(
    session: Session, socel: str, category: str
) -> None:
    taxonomies = GetClassTaxonomies().execute(GetClassTaxonomiesCommand())
    assert taxonomies is TAXONOMY
    assert any(root.contains(category) for root in taxonomies.flow_categories)
    definition = FlowDefinition(unit="kWh", category=category)
    preparation = PreparationValidator().prepare(
        PreparationDraft(flows={"heat": definition}),
        PreparationFacts(activities=frozenset(), object_types=frozenset(), flow_ids=frozenset()),
        record_flows=("heat",),
    )
    assert preparation.flows["heat"].category == category

    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.con.execute("UPDATE socel_flow SET category = ? WHERE flow_id = 'heat'", [category])
        with SOCEL.from_ocel(changed) as extension:
            extension.validate()
