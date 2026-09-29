"""What an SQLite file declares, compared with the sOCEL schema (Appendix A.1).

V1 asks for the four tables "with the declared types, primary keys, foreign
keys, and check constraints", and for the reserved attributes' declared types
where present. That is a property of the file, not of the data read from it:
data can be right in a file whose tables declare no constraints at all. The
declarations are read through `sqlite3`, the only reader that sees them.
"""

import re
import sqlite3
from contextlib import closing
from pathlib import Path

from socel.format.schema import RESERVED_ATTRIBUTES, TABLES, Table


def declared_schema_problems(path: Path) -> list[str]:
    """Where the file's declarations differ from the sOCEL schema; empty if they do not."""
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        sql = {
            str(name): str(ddl)
            for name, ddl in db.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'")
        }
        problems: list[str] = []
        for table in TABLES:
            if table.name in sql:
                problems += _table_problems(db, table, sql[table.name])
            else:
                problems.append(f"The file declares no table {table.name}.")
        problems += _reserved_attribute_problems(db, sql)
        return problems


def _table_problems(db: sqlite3.Connection, table: Table, ddl: str) -> list[str]:
    problems: list[str] = []
    # cid, name, type, notnull, default, pk (position in the primary key, from 1)
    info = {str(row[1]): row for row in db.execute(f"PRAGMA table_info({_quote(table.name)})")}

    for column in table.columns:
        row = info.get(column.name)
        if row is None:
            problems.append(f"{table.name} declares no column {column.name}.")
            continue
        declared = str(row[2] or "").upper()
        if declared != column.type:
            problems.append(
                f"{table.name}.{column.name} is declared {declared or 'without a type'}, "
                f"not {column.type}."
            )
        if not column.nullable and not row[3]:
            problems.append(f"{table.name}.{column.name} is not declared NOT NULL.")

    key = tuple(name for name, row in sorted(info.items(), key=lambda item: item[1][5]) if row[5])
    if key != table.primary_key:
        problems.append(
            f"{table.name} declares the primary key ({', '.join(key) or 'none'}), "
            f"not ({', '.join(table.primary_key)})."
        )

    # id, seq, table, from, to, ...
    references = {
        (str(row[3]), str(row[2]), str(row[4]))
        for row in db.execute(f"PRAGMA foreign_key_list({_quote(table.name)})")
    }
    for foreign_key in table.foreign_keys:
        expected = (
            foreign_key.column,
            foreign_key.references_table,
            foreign_key.references_column,
        )
        if expected not in references:
            problems.append(
                f"{table.name} declares no foreign key {foreign_key.column} -> "
                f"{foreign_key.references_table}({foreign_key.references_column})."
            )

    for check in table.checks:
        if _compact(f"CHECK ({check})") not in _compact(ddl):
            problems.append(f"{table.name} does not declare CHECK ({check}).")
    return problems


def _reserved_attribute_problems(db: sqlite3.Connection, sql: dict[str, str]) -> list[str]:
    """The reserved attributes' declared types, in every type table that has them."""
    problems: list[str] = []
    for entity in ("object", "event"):
        if f"{entity}_map_type" not in sql:
            continue
        attributes = [a for a in RESERVED_ATTRIBUTES if a.entity == entity]
        for (type_map,) in db.execute(f"SELECT ocel_type_map FROM {entity}_map_type"):
            table = f"{entity}_{type_map}"
            declared = {
                str(row[1]): str(row[2] or "").upper()
                for row in db.execute(f"PRAGMA table_info({_quote(table)})")
            }
            for attribute in attributes:
                if attribute.name in declared and declared[attribute.name] != attribute.type:
                    problems.append(
                        f"{table}.{attribute.name} is declared "
                        f"{declared[attribute.name] or 'without a type'}, not {attribute.type}."
                    )
    return problems


def _quote(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def _compact(sql: str) -> str:
    """SQL without whitespace and case, to compare declarations however they are laid out."""
    return re.sub(r"\s+", "", sql).lower()
