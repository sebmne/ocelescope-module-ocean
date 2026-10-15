from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ocelescope_module_socel.domain.models.analysis_window import AnalysisWindow


@pytest.mark.parametrize("end", [datetime(2026, 1, 1, 10), datetime(2026, 1, 1, 9)])
def test_a_window_must_have_positive_duration(end: datetime) -> None:
    with pytest.raises(ValidationError, match="start before it ends"):
        AnalysisWindow(start=datetime(2026, 1, 1, 10), end=end)


def test_window_timestamps_must_have_compatible_time_zones() -> None:
    with pytest.raises(ValidationError, match="compatible time zones"):
        AnalysisWindow(start=datetime(2026, 1, 1, 10), end=datetime(2026, 1, 1, 11, tzinfo=UTC))


def test_window_contains_its_start_and_excludes_its_end() -> None:
    window = AnalysisWindow(start=datetime(2026, 1, 1, 10), end=datetime(2026, 1, 1, 11))
    assert window.contains(window.start)
    assert window.contains(datetime(2026, 1, 1, 10, 30))
    assert not window.contains(window.end)
    assert not window.contains(datetime(2026, 1, 1, 9, 59))
