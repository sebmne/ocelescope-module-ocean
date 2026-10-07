"""Applying emission rules to an OCEL: the core of OCEAn's emission computation."""

from collections.abc import Sequence

import polars as pl
from ocelescope import OCEL

from ocelescope_module_ocean.domain.exceptions import InvalidEmissionRuleError, RuleProblem
from ocelescope_module_ocean.domain.models.attributes import (
    AttributeRef,
    EventAttributeRef,
    ObjectAttributeRef,
)
from ocelescope_module_ocean.domain.models.emission_rules import (
    E2OEmissionRule,
    EmissionRule,
    EventEmissionRule,
)
from ocelescope_module_ocean.domain.models.emissions import (
    EMISSIONS_KG,
    EmissionsOverview,
    ProcessEmissions,
)
from ocelescope_module_ocean.ocel_utils.values import (
    EID,
    OID,
    TIMESTAMP,
    events_of,
    object_values_at_events,
    relations_of,
)

_EVENT_SCHEMA = {EID: pl.String, EMISSIONS_KG: pl.Float64}
_E2O_SCHEMA = {EID: pl.String, OID: pl.String, EMISSIONS_KG: pl.Float64}


def compute_emissions(ocel: OCEL, rules: Sequence[EmissionRule]) -> ProcessEmissions:
    """Applies all rules and sums their results per event and per event-object pair.

    Raises:
        InvalidEmissionRuleError: A rule does not fit the OCEL.
    """
    event_results, e2o_results = [], []
    for index, rule in enumerate(rules):
        try:
            result = apply_rule(rule, ocel)
        except RuleProblem as problem:
            raise InvalidEmissionRuleError(index, str(problem)) from problem
        (e2o_results if isinstance(rule, E2OEmissionRule) else event_results).append(result)
    return combine_emissions(event_results, e2o_results)


def apply_rule(rule: EmissionRule, ocel: OCEL) -> pl.DataFrame:
    """The emissions of one rule: per event (event rules) or per relation (E2O rules).

    Raises:
        RuleProblem: The rule does not fit the OCEL.
    """
    match rule:
        case EventEmissionRule():
            return _apply_event_rule(rule, ocel)
        case E2OEmissionRule():
            return _apply_e2o_rule(rule, ocel)


def combine_emissions(
    event_results: Sequence[pl.DataFrame], e2o_results: Sequence[pl.DataFrame]
) -> ProcessEmissions:
    """Sums the results of several rules per event, and per event-object pair.

    Missing emissions (null) count as nothing, like in the original OCEAn.
    """
    events = pl.concat([pl.DataFrame(schema=_EVENT_SCHEMA), *event_results], how="vertical_relaxed")
    e2o = pl.concat([pl.DataFrame(schema=_E2O_SCHEMA), *e2o_results], how="vertical_relaxed")
    event_emissions = events.group_by(EID).agg(pl.col(EMISSIONS_KG).sum())
    e2o_emissions = e2o.group_by(EID, OID).agg(pl.col(EMISSIONS_KG).sum())
    return ProcessEmissions(
        event_emissions=event_emissions,
        e2o_emissions=e2o_emissions,
        total_kg=float(event_emissions[EMISSIONS_KG].sum())
        + float(e2o_emissions[EMISSIONS_KG].sum()),
    )


def summarize_emissions(emissions: ProcessEmissions | None) -> EmissionsOverview:
    """The totals of the emissions; all None if none were computed yet."""
    rule_based = emissions.total_kg if emissions else None
    # TODO: imported emissions (attributes of the OCEL that already hold emissions).
    return EmissionsOverview(rule_based_kg=rule_based, imported_kg=None, total_kg=rule_based)


def _apply_event_rule(rule: EventEmissionRule, ocel: OCEL) -> pl.DataFrame:
    """Emissions per event of the activity: ocel:eid, EMISSIONS_KG.

    An event whose attribute value is missing gets a null emission.
    """
    _check_activity(ocel, rule.activity)
    events, columns = _event_level_values(ocel, rule.activity, rule.factor.attributes)
    return events.select(EID, _emissions(rule.factor.value_kg, columns))


def _apply_e2o_rule(rule: E2OEmissionRule, ocel: OCEL) -> pl.DataFrame:
    """Emissions per relation: ocel:eid, ocel:oid, EMISSIONS_KG."""
    _check_activity(ocel, rule.activity)

    def is_own(attribute: AttributeRef) -> bool:
        """An attribute of the relation's own object."""
        return (
            isinstance(attribute, ObjectAttributeRef)
            and attribute.object_type == rule.object_type
            and attribute.qualifier in (None, rule.qualifier)
        )

    own = [a for a in rule.factor.attributes if is_own(a)]
    others = [a for a in rule.factor.attributes if not is_own(a)]

    relations = relations_of(ocel, rule.activity, rule.object_type, rule.qualifier)
    if relations.is_empty():
        raise RuleProblem(_no_relations(rule.activity, rule.object_type, rule.qualifier))

    # Attributes of each relation's own object, at the event's time.
    own_names = [a.name for a in own if isinstance(a, ObjectAttributeRef)]
    _check_object_attributes(ocel, own_names)
    if own_names:
        relations = object_values_at_events(ocel, relations, rule.object_type, own_names)
    renamed = {name: f"{rule.object_type} (own).{name}" for name in own_names}
    relations = relations.rename(renamed)

    # Everything else is the same for all relations of an event.
    events, event_columns = _event_level_values(ocel, rule.activity, others)
    rows = relations.join(events.drop(TIMESTAMP), on=EID, how="left")
    return rows.select(
        EID, OID, _emissions(rule.factor.value_kg, [*renamed.values(), *event_columns])
    )


# ---- Shared by both rule types ----------------------------------------------


def _check_activity(ocel: OCEL, activity: str) -> None:
    if activity not in ocel.events.activities:
        raise RuleProblem(f"Unknown activity '{activity}'.")


def _emissions(value_kg: float, columns: Sequence[str]) -> pl.Expr:
    """value_kg times every column; null as soon as one value is missing."""
    product = pl.lit(value_kg, dtype=pl.Float64)
    for column in columns:
        product = product * pl.col(column).cast(pl.Float64)
    return product.alias(EMISSIONS_KG)


def _event_level_values(
    ocel: OCEL, activity: str, attributes: Sequence[AttributeRef]
) -> tuple[pl.DataFrame, list[str]]:
    """The activity's events with one column per attribute: event attributes, and
    object attributes of objects the events relate to uniquely.

    Returns the frame (ocel:eid, ocel:timestamp, value columns) and the value
    columns' names.
    """
    event_attributes = [a for a in attributes if isinstance(a, EventAttributeRef)]
    object_attributes = [a for a in attributes if isinstance(a, ObjectAttributeRef)]

    _check_event_attributes(ocel, activity, event_attributes)
    events = events_of(ocel, activity, [a.name for a in event_attributes])
    columns = [a.name for a in event_attributes]

    # One join per related object type (and qualifier).
    groups: dict[tuple[str, str | None], list[str]] = {}
    for attribute in object_attributes:
        groups.setdefault((attribute.object_type, attribute.qualifier), []).append(attribute.name)
    for (object_type, qualifier), names in groups.items():
        values = _unique_object_values(ocel, activity, object_type, qualifier, names)
        renamed = {name: f"{object_type}/{qualifier or '*'}.{name}" for name in names}
        events = events.join(values.rename(renamed), on=EID, how="left")
        columns += renamed.values()
    return events, columns


def _check_event_attributes(ocel: OCEL, activity: str, attributes: list[EventAttributeRef]) -> None:
    schema = ocel.events.pl.collect_schema()
    for attribute in attributes:
        if attribute.name not in schema:
            raise RuleProblem(f"Events of '{activity}' have no attribute '{attribute.name}'.")
        if not schema[attribute.name].is_numeric():
            raise RuleProblem(f"Event attribute '{attribute.name}' is not numeric.")


def _check_object_attributes(ocel: OCEL, names: list[str]) -> None:
    schema = ocel.objects.changes_pl.collect_schema()
    for name in names:
        if name not in schema:
            raise RuleProblem(f"Objects have no attribute '{name}'.")
        if not schema[name].is_numeric():
            raise RuleProblem(f"Object attribute '{name}' is not numeric.")


def _no_relations(activity: str, object_type: str, qualifier: str | None) -> str:
    with_qualifier = f" with qualifier '{qualifier}'" if qualifier else ""
    return f"Events of '{activity}' relate to no '{object_type}' objects{with_qualifier}."


def _unique_object_values(
    ocel: OCEL, activity: str, object_type: str, qualifier: str | None, names: list[str]
) -> pl.DataFrame:
    """The attribute values of the one related object of the type, per event.

    Raises:
        RuleProblem: Some event relates to several such objects, or an attribute is
            unknown or not numeric.
    """
    _check_object_attributes(ocel, names)
    relations = relations_of(ocel, activity, object_type, qualifier)
    if relations.is_empty():
        raise RuleProblem(_no_relations(activity, object_type, qualifier))
    most_per_event = relations.group_by(EID).len()["len"].max()
    if isinstance(most_per_event, int) and most_per_event > 1:
        raise RuleProblem(
            f"Events of '{activity}' relate to up to {most_per_event} '{object_type}' objects;"
            " only attributes of a uniquely related object can be used per event."
        )

    values = object_values_at_events(ocel, relations, object_type, names)
    return values.select(EID, *names).unique(subset=EID, keep="first")
