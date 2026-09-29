"""SQL pieces the analyses share."""

from socel.format.schema import CONTAINED_IN


def seconds(later: str, earlier: str) -> str:
    """The time between two timestamp expressions, in seconds (a DOUBLE)."""
    return f"((epoch_ms({later}) - epoch_ms({earlier})) / 1000.0)"


def share(start: str, end: str, a: str, b: str) -> str:
    """The part of a span (start, end) that lies in the window (a, b), as a
    fraction of the span: a record's share of a window (Definition 6.1.1)."""
    return f"{seconds(f'least({end}, {b})', f'greatest({start}, {a})')} / {seconds(end, start)}"


def is_top_level(alias: str) -> str:
    """Whether the flow instance (alias.flow_id, alias.object_id) is contained in
    no other: the analyzed set G of Section 6.3, so nested scopes count once."""
    return f"""NOT EXISTS (
        SELECT 1 FROM {CONTAINED_IN.name} c
        WHERE c.flow_id = {alias}.flow_id AND c.object_id = {alias}.object_id)"""
