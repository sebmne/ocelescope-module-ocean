"""Preparation rules, independent of FastAPI, Ocelescope, and DuckDB."""

import pytest

from ocelescope_module_socel.domain.exceptions import (
    FlowNameTaken,
    InvalidFlowEdit,
    InvalidRecordFile,
    UndefinedFlow,
    UnknownCategory,
    UnknownClass,
    UnknownFlow,
    UnknownType,
)
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.domain.models.flow_edit import FlowEdit
from ocelescope_module_socel.domain.models.preparation import (
    Preparation,
    PreparationDraft,
    PreparationFacts,
    RecordsToImport,
)
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, FlowDefinition
from ocelescope_module_socel.domain.services.preparation_validator import PreparationValidator
from ocelescope_module_socel.domain.taxonomies import TAXONOMY


@pytest.fixture
def facts() -> PreparationFacts:
    return PreparationFacts(
        activities=frozenset({"mill"}),
        object_types=frozenset({"machine", "hall"}),
        flow_ids=frozenset({"power", "heat"}),
    )


def edit(flow_id: str, name: str, *, delete: bool = False) -> FlowEdit:
    return FlowEdit(flow_id=flow_id, name=name, unit="kWh", category="energy", delete=delete)


@pytest.mark.parametrize(
    ("mapping", "readable"),
    [
        ({}, False),
        ({"flow": "f", "object": "o", "quantity": "q"}, False),
        ({"flow": "f", "object": "o", "quantity": "q", "event": "e"}, True),
        ({"flow": "f", "object": "o", "quantity": "q", "startTime": "s", "endTime": "t"}, True),
        ({"event": "e", "endTime": "t"}, True),
        ({"event": "", "endTime": "t"}, False),
    ],
)
def test_mapping_owns_readability(mapping: dict[str, str], readable: bool) -> None:
    assert ColumnMapping.model_validate(mapping).is_readable() is readable


def test_a_draft_can_be_incomplete_but_executable_preparation_cannot() -> None:
    draft = PreparationDraft(records=RecordsToImport(upload_id="u", mapping=ColumnMapping()))
    with pytest.raises(InvalidRecordFile):
        Preparation.model_validate(draft.model_dump())


@pytest.mark.parametrize("conversion", [0.0, float("inf"), float("-inf"), float("nan")])
def test_invalid_conversions_fail_without_a_use_case(conversion: float) -> None:
    with pytest.raises(InvalidFlowEdit):
        FlowEdit(flow_id="heat", name="heat", unit="kWh", category="energy", conversion=conversion)


def test_flow_edit_normalizes_its_own_text_and_allows_direction_reversal() -> None:
    change = FlowEdit(
        flow_id="heat",
        name="  warmth ",
        unit=" kWh ",
        category="energy",
        external_ref="  ",
        conversion=-1,
    )
    assert (change.name, change.unit, change.external_ref, change.conversion) == (
        "warmth",
        "kWh",
        None,
        -1,
    )


def test_deletion_needs_no_replacement_definition() -> None:
    assert FlowEdit(flow_id="heat", name="", unit="", category=None, delete=True).delete


def test_blank_flow_names_are_invalid() -> None:
    with pytest.raises(InvalidFlowEdit, match="needs a name"):
        edit("heat", "  ")


def test_taxonomy_membership_is_exact_and_includes_intermediate_nodes() -> None:
    energy = TAXONOMY.flow_categories[0]
    assert energy.contains("energy")
    assert energy.contains("energy.electricity")
    assert not energy.contains("energy.electricity.custom")
    assert not energy.contains("electricity")
    assert not energy.contains("energy.")
    assert not energy.contains("energy..electricity")


def test_paths_come_from_nesting_without_storing_parent_state() -> None:
    leaf = ClassNode(label="gas")
    branch = ClassNode(label="auxiliary", children=(leaf,))
    assert branch.paths("material") == ("material.auxiliary", "material.auxiliary.gas")
    assert branch.paths("other") == ("other.auxiliary", "other.auxiliary.gas")
    assert branch.contains("auxiliary.gas")
    assert not branch.contains("material.auxiliary.gas")
    assert leaf.paths() == ("gas",)


def test_valid_preparation_preserves_class_removal(facts: PreparationFacts) -> None:
    result = PreparationValidator().prepare(
        PreparationDraft(activities={"mill": None}, object_types={"machine": "hu"}), facts
    )
    assert result.activities == {"mill": None}
    assert result.object_types == {"machine": "hu"}


@pytest.mark.parametrize(
    ("draft", "error"),
    [
        (PreparationDraft(activities={"missing": "op"}), UnknownType),
        (PreparationDraft(activities={"mill": "op.unknown"}), UnknownClass),
        (PreparationDraft(flow_edits=(edit("missing", "other"),)), UnknownFlow),
        (PreparationDraft(flow_edits=(edit("heat", "power"),)), FlowNameTaken),
        (PreparationDraft(flow_edits=(edit("heat", "a"), edit("heat", "b"))), InvalidFlowEdit),
    ],
)
def test_contextual_rules_reject_invalid_references(
    draft: PreparationDraft,
    error: type[Exception],
    facts: PreparationFacts,
) -> None:
    with pytest.raises(error):
        PreparationValidator().prepare(draft, facts)


@pytest.mark.parametrize(
    "changes",
    [
        (edit("heat", "power"), edit("power", "heat")),
        (edit("heat", "power"), edit("power", "power", delete=True)),
    ],
)
def test_names_can_be_swapped_or_reused_after_deletion(
    changes: tuple[FlowEdit, ...], facts: PreparationFacts
) -> None:
    result = PreparationValidator().prepare(PreparationDraft(flow_edits=changes), facts)
    assert result.flow_edits == changes


def test_only_usable_record_flows_require_definitions(facts: PreparationFacts) -> None:
    draft = PreparationDraft(
        flows={"new": FlowDefinition(unit="kWh", category="energy.electricity")}
    )
    assert PreparationValidator().prepare(draft, facts, record_flows=("new",)).flows == draft.flows
    with pytest.raises(UndefinedFlow, match="missing"):
        PreparationValidator().prepare(draft, facts, record_flows=("missing",))


def test_referenced_definition_category_is_validated(facts: PreparationFacts) -> None:
    draft = PreparationDraft(flows={"new": FlowDefinition(unit="kWh", category="unknown")})
    with pytest.raises(UnknownCategory):
        PreparationValidator().prepare(draft, facts, record_flows=("new",))


@pytest.mark.parametrize(
    "draft",
    [
        PreparationDraft(
            attribute_flows=(
                AttributeFlow(attribute="usage", flow_id="power", object_type="machine"),
            )
        ),
        PreparationDraft(
            containment=(
                TypeContainment(
                    object_type="machine", parent_type="hall", qualifier="in", flows=("power",)
                ),
            )
        ),
    ],
)
def test_attributes_and_containment_require_definitions(
    draft: PreparationDraft, facts: PreparationFacts
) -> None:
    with pytest.raises(UndefinedFlow):
        PreparationValidator().prepare(draft, facts)


def test_containment_references_known_object_types(facts: PreparationFacts) -> None:
    draft = PreparationDraft(
        containment=(
            TypeContainment(object_type="machine", parent_type="missing", qualifier="in", flows=()),
        )
    )
    with pytest.raises(UnknownType, match="missing"):
        PreparationValidator().prepare(draft, facts)
