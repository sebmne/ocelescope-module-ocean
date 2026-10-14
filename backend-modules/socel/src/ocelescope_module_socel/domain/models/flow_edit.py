from ocelescope_module_socel.domain.models.base import Model


class FlowEdit(Model):
    """A flow of the log as it is to be: its new name and definition, or gone.

    `conversion` multiplies every record's quantity, for a new unit: from kWh
    to MJ it is 3.6. None leaves the quantities as recorded.
    """

    flow_id: str
    name: str
    unit: str
    category: str | None
    external_ref: str | None = None
    conversion: float | None = None
    delete: bool = False
