"""Allocation to products and lineage propagation."""

from dataclasses import dataclass
from decimal import Decimal
from math import isclose

from ocelescope.ocel.constants.pm4py import (
    EID_COL,
    O2O_QUALIFIER,
    O2O_SOURCE_ID,
    O2O_TARGET_ID,
    OBJECT_CHANGED_FIELD,
    OID_COL,
    TIMESTAMP_COL,
)
from ocelescope.ocel.constants.tables import (
    E2O_TABLE,
    O2O_TABLE,
    OBJECT_CHANGES_TABLE,
)

from socel.analysis.attribution import AttributionScope, attribute
from socel.domain import FlowInstance
from socel.socel import SOCEL
from socel.validation.queries import identifier


@dataclass(frozen=True, slots=True)
class FlowSelection:
    """The flow instances selected for an analysis."""

    instances: frozenset[FlowInstance]

    def __post_init__(self) -> None:
        if any(
            not instance.object_id or not instance.flow_id
            for instance in self.instances
        ):
            raise ValueError("Selected flow instances must have non-empty identifiers.")

    def validate_for(self, socel: SOCEL) -> None:
        """Validate membership and non-overlap against one sOCEL."""
        unknown = sorted(
            (
                instance
                for instance in self.instances
                if socel.flow_instances.get(instance.object_id, instance.flow_id)
                is None
            ),
            key=_instance_key,
        )
        if unknown:
            examples = ", ".join(
                f"({instance.object_id}, {instance.flow_id})"
                for instance in unknown[:3]
            )
            raise ValueError(f"Unknown selected flow instance(s): {examples}.")

        for instance in self.instances:
            selected_ancestors = self.instances.intersection(
                socel.flow_instances.ancestors(instance)
            )
            if selected_ancestors:
                ancestor = min(selected_ancestors, key=_instance_key)
                raise ValueError(
                    "A flow selection cannot contain nested instances: "
                    f"({instance.object_id}, {instance.flow_id}) is contained in "
                    f"({ancestor.object_id}, {ancestor.flow_id})."
                )


@dataclass(frozen=True, slots=True)
class AllocationParameters:
    """The selected instances and optional attribution choices used for allocation."""

    selection: FlowSelection
    attribution_scopes: tuple[AttributionScope, ...] = ()

    def __post_init__(self) -> None:
        scoped_instances = [scope.flow_instance for scope in self.attribution_scopes]
        if len(scoped_instances) != len(set(scoped_instances)):
            raise ValueError("Each flow instance may have one attribution scope.")
        outside_selection = set(scoped_instances).difference(self.selection.instances)
        if outside_selection:
            raise ValueError("Attribution scopes must belong to the flow selection.")

    def attribution_scope_for(self, instance: FlowInstance) -> AttributionScope:
        """Return an explicit scope or the default scope for an instance."""
        return next(
            (
                scope
                for scope in self.attribution_scopes
                if scope.flow_instance == instance
            ),
            AttributionScope(instance),
        )


@dataclass(frozen=True, slots=True)
class FlowEventQuantity:
    """The attributed quantity of one flow at one event."""

    flow_id: str
    event_id: str
    quantity: float


@dataclass(frozen=True, slots=True)
class HandlingUnitQuantity:
    """A flow quantity assigned to one handling unit."""

    object_id: str
    quantity: float


@dataclass(frozen=True, slots=True)
class FlowAllocation:
    """Allocated quantities and remainder for one flow."""

    flow_id: str
    handling_units: tuple[HandlingUnitQuantity, ...]
    unallocated: float
    recorded: float

    def __post_init__(self) -> None:
        object_ids = [entry.object_id for entry in self.handling_units]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("A flow allocation must contain each handling unit once.")
        if not isclose(
            self.allocated + self.unallocated,
            self.recorded,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("Allocated and unallocated quantities must reconcile.")

    @property
    def allocated(self) -> float:
        return sum(entry.quantity for entry in self.handling_units)

    def for_handling_unit(self, object_id: str) -> float:
        return next(
            (
                entry.quantity
                for entry in self.handling_units
                if entry.object_id == object_id
            ),
            0.0,
        )


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """Allocation results grouped by flow."""

    flows: tuple[FlowAllocation, ...]

    def __post_init__(self) -> None:
        flow_ids = [flow.flow_id for flow in self.flows]
        if len(flow_ids) != len(set(flow_ids)):
            raise ValueError("An allocation result must contain each flow once.")

    def for_flow(self, flow_id: str) -> FlowAllocation | None:
        return next((flow for flow in self.flows if flow.flow_id == flow_id), None)


@dataclass(frozen=True, slots=True)
class LineageDefinition:
    """The OCEL relation and attribute that define handling-unit lineage."""

    creation_qualifier: str
    mass_attribute: str

    def __post_init__(self) -> None:
        if not self.creation_qualifier:
            raise ValueError("A creation qualifier must not be empty.")
        if not self.mass_attribute:
            raise ValueError("A mass attribute must not be empty.")


@dataclass(frozen=True, slots=True)
class FlowCarriedQuantity:
    """Carried quantities for one flow, retaining its unallocated remainder."""

    flow_id: str
    handling_units: tuple[HandlingUnitQuantity, ...]
    unallocated: float

    def for_handling_unit(self, object_id: str) -> float:
        return next(
            (
                entry.quantity
                for entry in self.handling_units
                if entry.object_id == object_id
            ),
            0.0,
        )


@dataclass(frozen=True, slots=True)
class CarriedQuantityResult:
    """Lineage-propagated quantities grouped by flow."""

    flows: tuple[FlowCarriedQuantity, ...]

    def for_flow(self, flow_id: str) -> FlowCarriedQuantity | None:
        return next((flow for flow in self.flows if flow.flow_id == flow_id), None)


def event_quantities(
    socel: SOCEL,
    parameters: AllocationParameters,
) -> tuple[FlowEventQuantity, ...]:
    """Aggregate attributed event quantities per flow over the selected instances."""
    parameters.selection.validate_for(socel)
    quantities: dict[tuple[str, str], float] = {}
    for instance in parameters.selection.instances:
        result = attribute(socel, parameters.attribution_scope_for(instance))
        for event in result.events:
            key = (instance.flow_id, event.event_id)
            quantities[key] = quantities.get(key, 0.0) + event.quantity
    return tuple(
        FlowEventQuantity(flow_id, event_id, event_quantity)
        for (flow_id, event_id), event_quantity in sorted(quantities.items())
    )


def allocate(socel: SOCEL, parameters: AllocationParameters) -> AllocationResult:
    """Allocate attributed flow quantities equally to participating handling units."""
    attributed = event_quantities(socel, parameters)
    allocated: dict[tuple[str, str], float] = {}
    for event_quantity in attributed:
        targets = _handling_units_for_event(socel, event_quantity.event_id)
        if not targets:
            continue
        target_quantity = event_quantity.quantity / len(targets)
        for object_id in targets:
            key = (event_quantity.flow_id, object_id)
            allocated[key] = allocated.get(key, 0.0) + target_quantity

    recorded: dict[str, float] = {}
    for instance in parameters.selection.instances:
        records = socel.measurements.for_instance(instance)
        recorded[instance.flow_id] = recorded.get(instance.flow_id, 0.0) + sum(
            (record.quantity for record in records),
            start=0.0,
        )

    flows: list[FlowAllocation] = []
    for flow_id, recorded_quantity in sorted(recorded.items()):
        handling_units = tuple(
            HandlingUnitQuantity(object_id, allocated_quantity)
            for (allocated_flow, object_id), allocated_quantity in sorted(
                allocated.items()
            )
            if allocated_flow == flow_id
        )
        allocated_quantity = sum(entry.quantity for entry in handling_units)
        flows.append(
            FlowAllocation(
                flow_id=flow_id,
                handling_units=handling_units,
                unallocated=recorded_quantity - allocated_quantity,
                recorded=recorded_quantity,
            )
        )
    return AllocationResult(tuple(flows))


def carry(
    socel: SOCEL,
    allocation: AllocationResult,
    definition: LineageDefinition,
) -> CarriedQuantityResult:
    """Propagate allocated quantities through handling-unit lineage by mass share."""
    handling_units = {
        classification.element_id
        for classification in socel.classifications.handling_units()
    }
    parents = _parents(socel, definition.creation_qualifier, handling_units)
    masses = _masses(socel, definition.mass_attribute, handling_units)
    _validate_lineage(parents)

    children: dict[str, set[str]] = {}
    for child, parent in parents.items():
        children.setdefault(parent, set()).add(child)
    mass_shares = {
        child: masses[child] / sum(masses[sibling] for sibling in siblings)
        for siblings in children.values()
        for child in siblings
    }

    flows: list[FlowCarriedQuantity] = []
    for flow in allocation.flows:
        relevant = handling_units.intersection(
            {entry.object_id for entry in flow.handling_units}
            | set(parents)
            | set(parents.values())
        )
        quantities = tuple(
            HandlingUnitQuantity(
                object_id,
                _carried_quantity(flow, object_id, parents, mass_shares),
            )
            for object_id in sorted(relevant)
        )
        flows.append(
            FlowCarriedQuantity(
                flow_id=flow.flow_id,
                handling_units=quantities,
                unallocated=flow.unallocated,
            )
        )
    return CarriedQuantityResult(tuple(flows))


def _handling_units_for_event(socel: SOCEL, event_id: str) -> tuple[str, ...]:
    rows = socel.ocel.con.execute(
        f"""
        SELECT DISTINCT {identifier(OID_COL)}
        FROM {identifier(E2O_TABLE)}
        WHERE {identifier(EID_COL)} = ?
        ORDER BY {identifier(OID_COL)}
        """,
        [event_id],
    ).fetchall()
    return tuple(
        object_id
        for (value,) in rows
        if (object_id := str(value))
        and (class_name := socel.classifications.object_class(object_id)) is not None
        and socel.taxonomies.object_classes.is_a(class_name, "hu")
    )


def _parents(
    socel: SOCEL,
    qualifier: str,
    handling_units: set[str],
) -> dict[str, str]:
    rows = socel.ocel.con.execute(
        f"""
        SELECT {identifier(O2O_SOURCE_ID)}, {identifier(O2O_TARGET_ID)}
        FROM {identifier(O2O_TABLE)}
        WHERE {identifier(O2O_QUALIFIER)} = ?
        """,
        [qualifier],
    ).fetchall()
    parents: dict[str, str] = {}
    for source, target in rows:
        child, parent = str(source), str(target)
        if child not in handling_units or parent not in handling_units:
            raise ValueError("Creation relations must connect handling units.")
        if child in parents and parents[child] != parent:
            raise ValueError(f"Handling unit {child!r} has more than one parent.")
        parents[child] = parent
    return parents


def _masses(
    socel: SOCEL,
    attribute: str,
    handling_units: set[str],
) -> dict[str, float]:
    columns = {
        str(row[0])
        for row in socel.ocel.con.execute(
            f"DESCRIBE {identifier(OBJECT_CHANGES_TABLE)}"
        ).fetchall()
    }
    if attribute not in columns:
        raise ValueError(f"Unknown mass attribute {attribute!r}.")

    rows = socel.ocel.con.execute(
        f"""
        WITH initial_mass AS (
            SELECT
                {identifier(OID_COL)},
                {identifier(attribute)},
                row_number() OVER (
                    PARTITION BY {identifier(OID_COL)}
                    ORDER BY {identifier(TIMESTAMP_COL)}
                ) AS occurrence
            FROM {identifier(OBJECT_CHANGES_TABLE)}
            WHERE {identifier(OBJECT_CHANGED_FIELD)} = ?
              AND {identifier(attribute)} IS NOT NULL
        )
        SELECT {identifier(OID_COL)}, {identifier(attribute)}
        FROM initial_mass
        WHERE occurrence = 1
        """,
        [attribute],
    ).fetchall()
    masses: dict[str, float] = {}
    for object_id, value in rows:
        if not isinstance(value, int | float | Decimal):
            raise TypeError(f"Mass of handling unit {object_id!r} must be numeric.")
        mass = float(value)
        if mass <= 0:
            raise ValueError(f"Mass of handling unit {object_id!r} must be positive.")
        masses[str(object_id)] = mass

    missing = sorted(handling_units.difference(masses))
    if missing:
        raise ValueError(
            f"Handling unit(s) without {attribute!r}: {', '.join(missing[:3])}."
        )
    return masses


def _validate_lineage(parents: dict[str, str]) -> None:
    for origin in parents:
        visited: set[str] = set()
        current = origin
        while current in parents:
            if current in visited:
                raise ValueError(
                    f"Handling-unit lineage contains a cycle at {current!r}."
                )
            visited.add(current)
            current = parents[current]


def _carried_quantity(
    allocation: FlowAllocation,
    object_id: str,
    parents: dict[str, str],
    mass_shares: dict[str, float],
) -> float:
    quantity = 0.0
    share = 1.0
    current = object_id
    while True:
        quantity += allocation.for_handling_unit(current) * share
        if current not in parents:
            return quantity
        share *= mass_shares[current]
        current = parents[current]


def _instance_key(instance: FlowInstance) -> tuple[str, str]:
    return instance.flow_id, instance.object_id
