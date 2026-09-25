"""Graphs over an OCEL's objects.

Independent of OCEAn: imports only ocelescope, polars and rustworkx (enforced by
import-linter), so it can move into Ocelescope's core as it is.
"""

from ocelescope_module_socel.ocel_graph.nearest import nearest_targets
from ocelescope_module_socel.ocel_graph.object_graph import ObjectGraph, build_object_graph

__all__ = ["ObjectGraph", "build_object_graph", "nearest_targets"]
