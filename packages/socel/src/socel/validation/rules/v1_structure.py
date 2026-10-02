"""V1: required extension tables, columns, types, values, and keys."""

from collections.abc import Mapping

from socel.schema import (
    SOCEL_CLASS,
    SOCEL_END_TIME,
    TABLES,
    Column,
    Table,
    has_logical_type,
)
from socel.validation.context import ValidationContext
from socel.validation.queries import count_query, identifier
from socel.validation.rule import RuleValidation, ValidationRule


class StructureRule(ValidationRule):
    code = "V1"

    def validate(self, context: ValidationContext) -> RuleValidation:
        messages: list[str] = []
        for table in TABLES:
            messages.extend(self._validate_table(context, table))
        messages.extend(self._validate_reserved_attributes(context))
        return self.from_messages(messages)

    def _validate_table(self, context: ValidationContext, table: Table) -> list[str]:
        columns = context.columns.get(table.name, {})
        if not columns:
            return [f"Required table {table.name!r} is missing."]

        messages = self._validate_columns(table, columns)
        if messages:
            return messages

        messages.extend(self._validate_required_values(context, table))
        messages.extend(self._validate_key(context, table))
        return messages

    @staticmethod
    def _validate_columns(table: Table, actual: Mapping[str, str]) -> list[str]:
        messages: list[str] = []
        for column in table.columns:
            actual_type = actual.get(column.name)
            if actual_type is None:
                messages.append(
                    f"Required column {table.name}.{column.name} is missing."
                )
            elif not has_logical_type(actual_type, column.type):
                messages.append(
                    f"Column {table.name}.{column.name} has type {actual_type}; "
                    f"expected {column.type}."
                )
        return messages

    @staticmethod
    def _validate_required_values(
        context: ValidationContext, table: Table
    ) -> list[str]:
        messages: list[str] = []
        for column in table.columns:
            if column.nullable:
                continue
            nulls = count_query(
                context.ocel,
                f"SELECT count(*) FROM {identifier(table.name)} "
                f"WHERE {identifier(column.name)} IS NULL",
            )
            if nulls:
                messages.append(
                    f"Column {table.name}.{column.name} contains {nulls} null value(s)."
                )
        return messages

    @staticmethod
    def _validate_key(context: ValidationContext, table: Table) -> list[str]:
        key = ", ".join(identifier(column) for column in table.key)
        duplicates = count_query(
            context.ocel,
            f"SELECT count(*) FROM ("
            f"SELECT {key} FROM {identifier(table.name)} "
            f"GROUP BY {key} HAVING count(*) > 1"
            f") AS duplicate_keys",
        )
        if not duplicates:
            return []
        return [
            f"Table {table.name} contains {duplicates} duplicated primary-key value(s)."
        ]

    @staticmethod
    def _validate_reserved_attributes(context: ValidationContext) -> list[str]:
        reserved: tuple[tuple[str, Column], ...] = (
            ("events", Column(SOCEL_CLASS, "text", nullable=True)),
            ("events", Column(SOCEL_END_TIME, "timestamp", nullable=True)),
            ("object_changes", Column(SOCEL_CLASS, "text", nullable=True)),
        )
        messages: list[str] = []
        for table, column in reserved:
            actual_type = context.columns.get(table, {}).get(column.name)
            if actual_type is not None and not has_logical_type(
                actual_type, column.type
            ):
                messages.append(
                    f"Reserved attribute {table}.{column.name} has type {actual_type}; "
                    f"expected {column.type}."
                )
        return messages
