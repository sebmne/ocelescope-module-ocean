from ocelescope_module_socel.api.models.pagination import Page
from ocelescope_module_socel.domain.models.flow_inventory import FlowInstanceRow


class FlowInstancePage(Page[FlowInstanceRow]):
    path: tuple[str, ...]
