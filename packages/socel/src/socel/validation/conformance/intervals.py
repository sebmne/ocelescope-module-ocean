"""Interval records on their own: each is a valid interval, and those of one flow
instance do not overlap. Intervals are half-open, [start_time, end_time), so
consecutive records may meet at a boundary."""

import polars as pl
from ocelescope import OCEL

from socel.format.schema import INTERVAL_RECORDS
from socel.validation.check import RowCheck, counted


class IntervalsAreValid(RowCheck):
    """V4: every interval record starts strictly before it ends."""

    id = "V4"
    title = "Every interval record starts before it ends"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return f"SELECT * FROM {INTERVAL_RECORDS.name} WHERE start_time >= end_time"

    def describe(self, rows: pl.DataFrame) -> str:
        return f"{counted(rows.height, 'interval record')} not starting before it ends."


class IntervalsDoNotOverlap(RowCheck):
    """V6: interval records of the same flow instance (object_id, flow_id) do not overlap.

    Records of different flow instances may overlap: a submeter and the meter it
    belongs to measure the same time twice, which containment makes explicit.
    """

    id = "V6"
    title = "Interval records of a flow instance do not overlap"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return f"""
            SELECT a.object_id, a.flow_id,
                   a.record_id, a.start_time, a.end_time,
                   b.record_id AS overlapping_record_id,
                   b.start_time AS overlapping_start_time, b.end_time AS overlapping_end_time
            FROM {INTERVAL_RECORDS.name} a
            JOIN {INTERVAL_RECORDS.name} b
              ON a.object_id = b.object_id AND a.flow_id = b.flow_id
             AND a.record_id < b.record_id
             AND a.start_time < b.end_time AND b.start_time < a.end_time
            ORDER BY a.object_id, a.flow_id, a.start_time
        """

    def describe(self, rows: pl.DataFrame) -> str:
        instances = rows.select("object_id", "flow_id").n_unique()
        pairs = counted(rows.height, "pair")
        return f"{pairs} of overlapping interval records, in {counted(instances, 'flow instance')}."
