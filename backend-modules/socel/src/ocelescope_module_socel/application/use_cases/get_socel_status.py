from datetime import datetime

from socel import SOCEL, IntervalRecord

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.domain.models.socel_status import SocelStatus


class GetSocelStatusCommand(Command):
    socel: SOCEL


class GetSocelStatus:
    """What the sOCEL holds, in counts, and the period its records span."""

    def execute(self, command: GetSocelStatusCommand) -> SocelStatus:
        socel = command.socel
        records = socel.measurements.all()
        intervals = [record for record in records if isinstance(record, IntervalRecord)]
        instances = socel.flow_instances.all()

        # Interval records span their interval; event records sit at their event.
        event_ids = {
            record.event_id for record in records if not isinstance(record, IntervalRecord)
        }
        times = [
            *(record.start for record in intervals),
            *(record.end for record in intervals),
            *(
                datetime.fromisoformat(socel.events.get_event_timestamp(event_id))
                for event_id in event_ids
            ),
        ]
        return SocelStatus(
            objects=socel.objects.count,
            events=socel.events.count,
            handling_units=len(socel.classifications.handling_units()),
            operations=len(socel.classifications.operations()),
            flows=len(socel.flows.all()),
            flow_instances=len(instances),
            interval_records=len(intervals),
            event_records=len(records) - len(intervals),
            containments=sum(
                1 for instance in instances if socel.flow_instances.parent(instance) is not None
            ),
            records_from=min(times, default=None),
            records_to=max(times, default=None),
        )
