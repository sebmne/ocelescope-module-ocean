from collections import Counter

from socel import SOCEL, IntervalRecord

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.domain.models.flow_inventory import (
    FlowInstanceSummary,
    FlowSummary,
)


class GetFlowInventoryCommand(Command):
    socel: SOCEL


class GetFlowInventory:
    """The flows of an sOCEL, each with its flow instances: where they sit among the
    metering scopes (containment) and how many records they have."""

    def execute(self, command: GetFlowInventoryCommand) -> tuple[FlowSummary, ...]:
        socel = command.socel
        object_types = socel.objects.type_by_id.to_dict()
        intervals: Counter[tuple[str, str]] = Counter()
        events: Counter[tuple[str, str]] = Counter()
        for record in socel.measurements.all():
            key = (record.instance.object_id, record.instance.flow_id)
            (intervals if isinstance(record, IntervalRecord) else events)[key] += 1

        def summary(flow_id: str) -> tuple[FlowInstanceSummary, ...]:
            summaries = []
            for instance in socel.flow_instances.for_flow(flow_id):
                parent = socel.flow_instances.parent(instance)
                key = (instance.object_id, instance.flow_id)
                summaries.append(
                    FlowInstanceSummary(
                        object_id=instance.object_id,
                        object_type=str(object_types.get(instance.object_id, "")),
                        parent_object_id=parent.object_id if parent else None,
                        interval_records=intervals[key],
                        event_records=events[key],
                    )
                )
            return tuple(sorted(summaries, key=lambda item: item.object_id))

        return tuple(
            FlowSummary(
                flow_id=flow.id,
                unit=flow.unit,
                category=flow.category,
                external_ref=flow.external_ref,
                instances=summary(flow.id),
            )
            for flow in socel.flows.all()
        )
