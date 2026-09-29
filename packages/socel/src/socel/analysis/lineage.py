"""The lineage of handling units (Definition 6.3.3): which unit was created from
which, their masses at creation, and the quantities they carry along it.

Which O2O qualifier encodes creation and which attribute is the mass are
parameters of the analysis (Section 6.3); the source of such a relation is
created from its target, as in the running example's `from part`.
"""

from collections.abc import Mapping

import polars as pl

from socel._ocelescope import (
    CHANGE_COLUMNS,
    O2O,
    O2O_SOURCE,
    O2O_TARGET,
    OBJECT_CHANGES,
    OID,
    QUALIFIER,
    TIME,
    column_type,
    ident,
)
from socel.errors import LineageError
from socel.format.attributes import objects_sql
from socel.model.socel import SOCEL

_NUMERIC = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL")


def unit_relation_qualifiers(socel: SOCEL) -> pl.DataFrame:
    """The O2O qualifiers relating a handling unit to another: qualifier, relations."""
    units = f"(SELECT object_id FROM ({objects_sql(socel.ocel)}) WHERE is_handling_unit)"
    return socel.sql(f"""
        SELECT {ident(QUALIFIER)} AS qualifier, count(*) AS relations
        FROM {O2O}
        WHERE {ident(O2O_SOURCE)} IN {units} AND {ident(O2O_TARGET)} IN {units}
        GROUP BY ALL ORDER BY relations DESC, qualifier
    """).pl()


def unit_attributes(socel: SOCEL) -> pl.DataFrame:
    """The numeric attributes some handling unit has a value of: attribute, units."""
    columns = [
        name
        for (name,) in socel.sql(
            "SELECT column_name FROM information_schema.columns "
            f"WHERE table_schema = 'main' AND table_name = '{OBJECT_CHANGES}'"
        ).fetchall()
        if name not in CHANGE_COLUMNS
        and (column_type(socel.ocel, OBJECT_CHANGES, name) or "").startswith(_NUMERIC)
    ]
    if not columns:
        return pl.DataFrame(schema={"attribute": pl.String, "units": pl.Int64})
    units = f"(SELECT object_id FROM ({objects_sql(socel.ocel)}) WHERE is_handling_unit)"
    counts = ", ".join(
        f"count(DISTINCT {ident(OID)}) FILTER (WHERE {ident(c)} IS NOT NULL)" for c in columns
    )
    row = socel.sql(
        f"SELECT {counts} FROM {OBJECT_CHANGES} WHERE {ident(OID)} IN {units}"
    ).fetchone()
    counted = zip(columns, row or [0] * len(columns), strict=True)
    return pl.DataFrame(
        [{"attribute": c, "units": int(n)} for c, n in counted if n],
        schema={"attribute": pl.String, "units": pl.Int64},
    ).sort("units", "attribute", descending=[True, False])


def parents(socel: SOCEL, qualifier: str) -> pl.DataFrame:
    """parent ∈ HU ↛ HU from the O2O relations with the qualifier: object_id,
    parent_object_id, both handling units.

    Raises:
        LineageError: A unit has several parents, or the relation has a cycle.
    """
    units = f"(SELECT object_id FROM ({objects_sql(socel.ocel)}) WHERE is_handling_unit)"
    relation = socel.sql(
        f"""
        SELECT DISTINCT {ident(O2O_SOURCE)} AS object_id, {ident(O2O_TARGET)} AS parent_object_id
        FROM {O2O}
        WHERE {ident(QUALIFIER)} = ?
          AND {ident(O2O_SOURCE)} IN {units} AND {ident(O2O_TARGET)} IN {units}
        """,
        [qualifier],
    ).pl()
    several = relation.group_by("object_id").len().filter(pl.col("len") > 1)["object_id"]
    if len(several):
        raise LineageError(
            f"{len(several)} handling units have several parents by {qualifier!r}, "
            f"e.g. {', '.join(sorted(several.to_list())[:3])}."
        )
    parent = dict(relation.iter_rows())
    for start in parent:
        seen = {start}
        unit = parent.get(start)
        while unit is not None:
            if unit in seen:
                raise LineageError(f"{qualifier!r} has a cycle through {start!r}.")
            seen.add(unit)
            unit = parent.get(unit)
    return relation.sort("object_id")


def creation_values(socel: SOCEL, attribute: str) -> pl.DataFrame:
    """Each object's first recorded value of an attribute - its value at creation:
    object_id, value.

    Raises:
        ValueError: No numeric object attribute of that name.
    """
    kind = column_type(socel.ocel, OBJECT_CHANGES, attribute) or ""
    if attribute in CHANGE_COLUMNS or not kind.startswith(_NUMERIC):
        raise ValueError(f"There is no numeric object attribute {attribute!r}.")
    return socel.sql(f"""
        SELECT {ident(OID)} AS object_id,
               arg_min({ident(attribute)}, {ident(TIME)})::DOUBLE AS value
        FROM {OBJECT_CHANGES} WHERE {ident(attribute)} IS NOT NULL
        GROUP BY ALL
    """).pl()


def carry(by_unit: pl.DataFrame, parent: pl.DataFrame, mass: pl.DataFrame) -> pl.DataFrame:
    """carr^G_f (Definition 6.3.3): a unit's own allocated quantity plus, down its
    lineage, its mass share of each ancestor's - carr(h) = alloc(h) + sh(h)·carr(parent(h)).

    Args:
        by_unit: flow_id, object_id, quantity - alloc^G_f (Allocation.by_unit).
        parent: object_id, parent_object_id (`parents`).
        mass: object_id, value (`creation_values`).

    Returns:
        flow_id, object_id, quantity, is_end - for every unit reached, where
        is_end marks the units without children. Over the end units, carr sums
        to the allocated total.

    Raises:
        LineageError: A unit created from another, or a sibling of one, has no
            positive mass.
    """
    parent_of: dict[str, str] = dict(parent.iter_rows())
    masses: dict[str, float] = {str(k): float(v) for k, v in mass.iter_rows()}
    children: dict[str, list[str]] = {}
    for child, of in parent_of.items():
        children.setdefault(of, []).append(child)
    lacking = sorted(
        c for siblings in children.values() for c in siblings if masses.get(c, 0.0) <= 0
    )
    if lacking:
        raise LineageError(
            f"{len(lacking)} created units have no positive mass, e.g. {', '.join(lacking[:3])}."
        )
    share = {
        child: masses[child] / sum(masses[s] for s in siblings)
        for siblings in children.values()
        for child in siblings
    }

    rows: list[dict[str, object]] = []
    for (flow_id,), allocated in by_unit.group_by("flow_id"):
        alloc = {str(k): float(v) for k, v in allocated.select("object_id", "quantity").iter_rows()}
        reached = set(alloc) | {c for u in alloc for c in _descendants(u, children)}
        carried: dict[str, float] = {}
        for unit in sorted(reached):
            rows.append(
                {
                    "flow_id": flow_id,
                    "object_id": unit,
                    "quantity": _carried(unit, alloc, parent_of, share, carried),
                    "is_end": unit not in children,
                }
            )
    return pl.DataFrame(
        rows,
        schema={
            "flow_id": pl.String,
            "object_id": pl.String,
            "quantity": pl.Float64,
            "is_end": pl.Boolean,
        },
    )


def _carried(
    unit: str,
    alloc: Mapping[str, float],
    parent_of: Mapping[str, str],
    share: Mapping[str, float],
    carried: dict[str, float],
) -> float:
    """carr(unit), filling `carried` along its lineage: up to the first unit known
    (or the root), then back down. Iterative, as lineages can be long."""
    path: list[str] = []
    current: str | None = unit
    while current is not None and current not in carried:
        path.append(current)
        current = parent_of.get(current)
    for member in reversed(path):
        up = parent_of.get(member)
        inherited = share[member] * carried[up] if up is not None else 0.0
        carried[member] = alloc.get(member, 0.0) + inherited
    return carried[unit]


def _descendants(unit: str, children: Mapping[str, list[str]]) -> set[str]:
    found: set[str] = set()
    stack = list(children.get(unit, ()))
    while stack:
        child = stack.pop()
        if child not in found:
            found.add(child)
            stack.extend(children.get(child, ()))
    return found
