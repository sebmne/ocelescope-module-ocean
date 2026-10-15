"""Query preparation belongs to the operation; its command only carries input."""

from unittest.mock import Mock

import pytest

from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.application.use_cases.get_flow_instances import (
    GetFlowInstances,
    GetFlowInstancesCommand,
)


@pytest.mark.parametrize(("offset", "limit"), [(-1, 1), (0, 0)])
def test_invalid_ranges_are_refused_before_reading(offset: int, limit: int) -> None:
    statistics = Mock(spec=SocelStatistics)
    with pytest.raises(ValueError):
        GetFlowInstances(statistics=statistics).execute(
            GetFlowInstancesCommand(flow_id="power", offset=offset, limit=limit)
        )
    statistics.flow_instances.assert_not_called()


def test_query_choices_are_normalized_without_changing_the_command() -> None:
    statistics = Mock(spec=SocelStatistics)
    statistics.flow_instances.return_value = ((), 0, ())
    command = GetFlowInstancesCommand(
        flow_id="power", offset=0, limit=1, search=" m1 ", inside="", object_type=""
    )

    assert GetFlowInstances(statistics=statistics).execute(command) == ((), 0, ())
    statistics.flow_instances.assert_called_once_with(
        "power", offset=0, limit=1, search="m1", inside=None, object_type=None, order="quantity"
    )
    assert (command.search, command.inside, command.object_type) == (" m1 ", "", "")
