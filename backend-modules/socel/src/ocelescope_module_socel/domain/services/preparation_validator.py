from collections import Counter
from collections.abc import Mapping, Sequence

from ocelescope_module_socel.domain.exceptions import (
    FlowNameTaken,
    UndefinedFlow,
    UnknownCategory,
    UnknownClass,
    UnknownFlow,
    UnknownType,
)
from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode
from ocelescope_module_socel.domain.models.preparation import (
    Preparation,
    PreparationDraft,
    PreparationFacts,
)
from ocelescope_module_socel.domain.taxonomies import TAXONOMY


class PreparationValidator:
    """Validate references and resulting flow names against supplied facts.

    Model construction owns local validity. This calculation spans the draft,
    log facts, record preview, and taxonomy; it performs no I/O.
    """

    def prepare(
        self,
        draft: PreparationDraft,
        facts: PreparationFacts,
        *,
        record_flows: Sequence[str] = (),
    ) -> Preparation:
        preparation = Preparation.model_validate(draft.model_dump(by_alias=False))
        self._classes("activity", preparation.activities, facts.activities, TAXONOMY.event_classes)
        self._classes(
            "object type", preparation.object_types, facts.object_types, TAXONOMY.object_classes
        )
        edits = {edit.flow_id: edit for edit in preparation.flow_edits}
        for edit in preparation.flow_edits:
            if edit.flow_id not in facts.flow_ids:
                raise UnknownFlow(edit.flow_id)
            if not edit.delete and edit.category is not None:
                self._category(edit.category)
        names = Counter(
            edits[flow_id].name if flow_id in edits else flow_id
            for flow_id in sorted(facts.flow_ids)
            if not (flow_id in edits and edits[flow_id].delete)
        )
        for name, count in names.items():
            if count > 1:
                raise FlowNameTaken(name)

        required = list(record_flows)
        for flow in preparation.attribute_flows:
            if flow.object_type not in facts.object_types:
                raise UnknownType("object type", flow.object_type)
            required.append(flow.flow_id)
        for containment in preparation.containment:
            for name in (containment.object_type, containment.parent_type):
                if name not in facts.object_types:
                    raise UnknownType("object type", name)
            required.extend(containment.flows)
        for flow_id in dict.fromkeys(required):
            definition = preparation.flows.get(flow_id)
            if not flow_id.strip() or definition is None or not definition.unit.strip():
                raise UndefinedFlow(flow_id)
            self._category(definition.category)
        return preparation

    def _classes(
        self,
        kind: str,
        choices: Mapping[str, str | None],
        known: frozenset[str],
        roots: tuple[ClassNode, ...],
    ) -> None:
        for name, path in choices.items():
            if name not in known:
                raise UnknownType(kind, name)
            if path is not None and not any(root.contains(path) for root in roots):
                raise UnknownClass(kind, path)

    def _category(self, category: str) -> None:
        if not any(root.contains(category) for root in TAXONOMY.flow_categories):
            raise UnknownCategory(category)
