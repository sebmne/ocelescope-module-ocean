"""Navigate sOCEL classifications on OCEL objects and events."""

from ocelescope.ocel.constants.pm4py import (
    EID_COL,
    OBJECT_CHANGED_FIELD,
    OID_COL,
    TIMESTAMP_COL,
)
from ocelescope.ocel.constants.tables import EVENTS_TABLE, OBJECT_CHANGES_TABLE
from ocelescope.ocel.managers.base import BaseManager

from socel.domain import Classification, ClassifiedElement
from socel.schema import SOCEL_CLASS


class ClassificationsManager(BaseManager):
    """Interpret the reserved ``socel_class`` attributes."""

    def object_class(self, object_id: str) -> str | None:
        """Return the current sOCEL class of an object."""
        if not self._has_column(OBJECT_CHANGES_TABLE, SOCEL_CLASS):
            return None
        row = self._relation(
            f"""
            SELECT {SOCEL_CLASS}
            FROM {OBJECT_CHANGES_TABLE}
            WHERE "{OID_COL}" = ?
              AND "{OBJECT_CHANGED_FIELD}" = ?
            ORDER BY "{TIMESTAMP_COL}" DESC
            LIMIT 1
            """,
            [object_id, SOCEL_CLASS],
        ).fetchone()
        return self._class_name(row)

    def event_class(self, event_id: str) -> str | None:
        """Return the sOCEL class of an event."""
        if not self._has_column(EVENTS_TABLE, SOCEL_CLASS):
            return None
        row = self._relation(
            f"""
            SELECT {SOCEL_CLASS}
            FROM {EVENTS_TABLE}
            WHERE "{EID_COL}" = ? AND {SOCEL_CLASS} IS NOT NULL
            """,
            [event_id],
        ).fetchone()
        return self._class_name(row)

    def objects(self, prefix: str | None = None) -> tuple[Classification, ...]:
        """Return classified objects, optionally below a class prefix."""
        if not self._has_column(OBJECT_CHANGES_TABLE, SOCEL_CLASS):
            return ()
        prefix_filter = (
            f"AND ({SOCEL_CLASS} = ? OR {SOCEL_CLASS} LIKE ?)"
            if prefix is not None
            else ""
        )
        params: list[object] = [SOCEL_CLASS]
        if prefix is not None:
            params.extend((prefix, f"{prefix}.%"))
        rows = self._relation(
            f"""
            WITH current_classes AS (
                SELECT
                    "{OID_COL}",
                    {SOCEL_CLASS},
                    row_number() OVER (
                        PARTITION BY "{OID_COL}" ORDER BY "{TIMESTAMP_COL}" DESC
                    ) AS recency
                FROM {OBJECT_CHANGES_TABLE}
                WHERE "{OBJECT_CHANGED_FIELD}" = ?
            )
            SELECT "{OID_COL}", {SOCEL_CLASS}
            FROM current_classes
            WHERE recency = 1
              AND {SOCEL_CLASS} IS NOT NULL
              {prefix_filter}
            ORDER BY "{OID_COL}"
            """,
            params,
        ).fetchall()
        return tuple(self._classification("object", row) for row in rows)

    def events(self, prefix: str | None = None) -> tuple[Classification, ...]:
        """Return classified events, optionally below a class prefix."""
        if not self._has_column(EVENTS_TABLE, SOCEL_CLASS):
            return ()
        prefix_filter = (
            f"AND ({SOCEL_CLASS} = ? OR {SOCEL_CLASS} LIKE ?)"
            if prefix is not None
            else ""
        )
        params: list[object] | None = (
            [prefix, f"{prefix}.%"] if prefix is not None else None
        )
        rows = self._relation(
            f"""
            SELECT "{EID_COL}", {SOCEL_CLASS}
            FROM {EVENTS_TABLE}
            WHERE {SOCEL_CLASS} IS NOT NULL
              {prefix_filter}
            ORDER BY "{EID_COL}"
            """,
            params,
        ).fetchall()
        return tuple(self._classification("event", row) for row in rows)

    def handling_units(self) -> tuple[Classification, ...]:
        """Return objects classified as handling units."""
        return self.objects("hu")

    def process_resources(self) -> tuple[Classification, ...]:
        """Return objects classified as process resources."""
        return self.objects("pr")

    def operations(self) -> tuple[Classification, ...]:
        """Return events classified as operations."""
        return self.events("op")

    def _has_column(self, table: str, column: str) -> bool:
        return bool(
            self._relation(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = ? AND column_name = ?
                """,
                [table, column],
            ).fetchone()
        )

    @staticmethod
    def _class_name(row: tuple[object, ...] | None) -> str | None:
        if row is None or row[0] is None:
            return None
        if not isinstance(row[0], str):
            raise TypeError("An sOCEL class must be a string.")
        return row[0]

    @staticmethod
    def _classification(
        element: ClassifiedElement, row: tuple[object, ...]
    ) -> Classification:
        element_id, name = row
        if not isinstance(element_id, str) or not isinstance(name, str):
            raise TypeError("A classification must contain strings.")
        return Classification(element=element, element_id=element_id, name=name)
