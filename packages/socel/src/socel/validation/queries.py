"""Stateless database queries shared by validation rules."""

from collections.abc import Sequence
from dataclasses import dataclass

from ocelescope import OCEL


def identifier(value: str) -> str:
    """Quote a trusted schema identifier for DuckDB."""
    return '"' + value.replace('"', '""') + '"'


def inspect_columns(ocel: OCEL) -> dict[str, dict[str, str]]:
    """Read the complete table/column schema once for a validation run."""
    rows = ocel.con.execute(
        "SELECT table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema = current_schema()"
    ).fetchall()

    tables: dict[str, dict[str, str]] = {}
    for table, column, data_type in rows:
        tables.setdefault(str(table), {})[str(column)] = str(data_type)
    return tables


def count_query(ocel: OCEL, query: str, parameters: Sequence[object] = ()) -> int:
    """Execute a count query and verify its scalar result."""
    row = ocel.con.execute(query, list(parameters)).fetchone()
    if row is None:
        return 0

    count = row[0]
    if not isinstance(count, int):
        raise TypeError(f"Expected an integer count, received {type(count).__name__}.")
    return count


@dataclass(frozen=True)
class QuerySummary:
    count: int
    examples: tuple[tuple[object, ...], ...]

    @property
    def example_text(self) -> str:
        return ", ".join(
            "/".join(str(value) for value in example) for example in self.examples
        )


def summarize_query(
    ocel: OCEL,
    query: str,
    parameters: Sequence[object] = (),
    *,
    example_limit: int = 3,
) -> QuerySummary:
    """Count rows returned by ``query`` and retain a small example set."""
    count = count_query(
        ocel,
        f"SELECT count(*) FROM ({query}) AS violations",
        parameters,
    )
    if count == 0:
        return QuerySummary(0, ())

    rows = ocel.con.execute(
        f"SELECT * FROM ({query}) AS violations LIMIT {example_limit}",
        list(parameters),
    ).fetchall()
    return QuerySummary(count, tuple(tuple(row) for row in rows))
