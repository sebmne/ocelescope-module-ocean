from collections.abc import Sequence

from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import (
    O2O_QUALIFIER,
    O2O_SOURCE_ID,
    O2O_TARGET_ID,
    OID_COL,
    OTYPE_COL,
)
from ocelescope.ocel.constants.tables import O2O_TABLE, OBJECTS_TABLE

from ocelescope_module_socel.domain.exceptions import SeveralParents
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.infrastructure.schema import CONTAINED_IN


class DuckDbContainmentWriter:
    """Turns containment between object types into rows with SQL on the log's DuckDB database:
    one query per pair of types and flow, none per object."""

    def write(self, ocel: OCEL, containments: Sequence[TypeContainment]) -> None:
        con = ocel.con.cursor()
        try:
            con.execute(
                "CREATE TEMP TABLE new_containment "
                "(flow_id VARCHAR, object_id VARCHAR, parent_object_id VARCHAR)"
            )
            for containment in containments:
                for flow_id in containment.flows:
                    con.execute(
                        f"""
                        INSERT INTO new_containment
                        SELECT DISTINCT ?, relation."{O2O_SOURCE_ID}", relation."{O2O_TARGET_ID}"
                        FROM {O2O_TABLE} relation
                        JOIN {OBJECTS_TABLE} inner_object
                          ON inner_object."{OID_COL}" = relation."{O2O_SOURCE_ID}"
                        JOIN {OBJECTS_TABLE} outer_object
                          ON outer_object."{OID_COL}" = relation."{O2O_TARGET_ID}"
                        WHERE relation."{O2O_QUALIFIER}" = ?
                          AND inner_object."{OTYPE_COL}" = ?
                          AND outer_object."{OTYPE_COL}" = ?
                        """,
                        [
                            flow_id,
                            containment.qualifier,
                            containment.object_type,
                            containment.parent_type,
                        ],
                    )
            # Together with what the log holds already: an object lies inside
            # one object per flow at most.
            several = con.execute(
                f"""
                SELECT flow_id, count(*), min(object_id) FROM (
                    SELECT flow_id, object_id FROM (
                        SELECT flow_id, object_id, parent_object_id FROM new_containment
                        UNION SELECT flow_id, object_id, parent_object_id FROM {CONTAINED_IN.name}
                    )
                    GROUP BY 1, 2 HAVING count(DISTINCT parent_object_id) > 1
                ) GROUP BY 1 ORDER BY 1 LIMIT 1
                """
            ).fetchone()
            if several is not None:
                raise SeveralParents(*several)
            con.execute(
                f"""
                INSERT INTO {CONTAINED_IN.name} (flow_id, object_id, parent_object_id)
                SELECT DISTINCT flow_id, object_id, parent_object_id FROM new_containment
                EXCEPT SELECT flow_id, object_id, parent_object_id FROM {CONTAINED_IN.name}
                """
            )
        finally:
            con.close()
