"""Expected-flow signatures connecting class and flow taxonomies."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from socel.taxonomy.model import Taxonomy


class FlowDirection(StrEnum):
    INPUT = "in"
    OUTPUT = "out"


class ClassDomain(StrEnum):
    EVENT = "event"
    OBJECT = "object"


@dataclass(frozen=True, slots=True)
class ExpectedFlow:
    """One flow-category expectation in a class signature."""

    category_id: str
    direction: FlowDirection
    alternative_group: str | None = None
    condition_category_id: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ClassSignature:
    """Expected flows directly attached to one event or object class."""

    domain: ClassDomain
    class_id: str
    expected_flows: tuple[ExpectedFlow, ...] = ()


@dataclass(frozen=True, slots=True, init=False)
class SignatureCatalog:
    """Immutable signatures with class-tree inheritance."""

    _flow_categories: Taxonomy = field(repr=False)
    _object_classes: Taxonomy = field(repr=False)
    _event_classes: Taxonomy = field(repr=False)
    _object_signatures: Mapping[str, tuple[ExpectedFlow, ...]] = field(repr=False)
    _event_signatures: Mapping[str, tuple[ExpectedFlow, ...]] = field(repr=False)

    def __init__(
        self,
        flow_categories: Taxonomy,
        object_classes: Taxonomy,
        event_classes: Taxonomy,
        signatures: Iterable[ClassSignature] = (),
    ) -> None:
        object_signatures: dict[str, tuple[ExpectedFlow, ...]] = {}
        event_signatures: dict[str, tuple[ExpectedFlow, ...]] = {}

        for signature in signatures:
            taxonomy, target = (
                (event_classes, event_signatures)
                if signature.domain is ClassDomain.EVENT
                else (object_classes, object_signatures)
            )
            taxonomy.require(signature.class_id)
            if signature.class_id in target:
                raise ValueError(
                    f"Duplicate signature for {signature.domain.value} class "
                    f"{signature.class_id!r}."
                )
            for expected in signature.expected_flows:
                flow_categories.require(expected.category_id)
                if expected.condition_category_id is not None:
                    flow_categories.require(expected.condition_category_id)
            target[signature.class_id] = signature.expected_flows

        object.__setattr__(self, "_flow_categories", flow_categories)
        object.__setattr__(self, "_object_classes", object_classes)
        object.__setattr__(self, "_event_classes", event_classes)
        object.__setattr__(
            self, "_object_signatures", MappingProxyType(object_signatures)
        )
        object.__setattr__(
            self, "_event_signatures", MappingProxyType(event_signatures)
        )

    def for_event_class(
        self, class_id: str, *, inherited: bool = True
    ) -> ClassSignature | None:
        """Return the effective signature of an operation class."""
        return self._signature(
            ClassDomain.EVENT,
            self._event_classes,
            self._event_signatures,
            class_id,
            inherited,
        )

    def for_object_class(
        self, class_id: str, *, inherited: bool = True
    ) -> ClassSignature | None:
        """Return the effective signature of a process-resource class."""
        return self._signature(
            ClassDomain.OBJECT,
            self._object_classes,
            self._object_signatures,
            class_id,
            inherited,
        )

    @staticmethod
    def _signature(
        domain: ClassDomain,
        taxonomy: Taxonomy,
        signatures: Mapping[str, tuple[ExpectedFlow, ...]],
        class_id: str,
        inherited: bool,
    ) -> ClassSignature | None:
        if class_id not in taxonomy:
            return None

        class_ids = [class_id]
        if inherited:
            class_ids = [
                *reversed(taxonomy.ancestors(class_id)),
                class_id,
            ]

        expected: list[ExpectedFlow] = []
        for current_id in class_ids:
            for entry in signatures.get(current_id, ()):
                if entry not in expected:
                    expected.append(entry)
        return ClassSignature(domain, class_id, tuple(expected))
