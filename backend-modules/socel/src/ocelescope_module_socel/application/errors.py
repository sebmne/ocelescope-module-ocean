class FlowNotFound(LookupError):
    """The flow addressed by a read operation does not exist in this view."""

    def __init__(self, flow_id: str) -> None:
        super().__init__(f"The log has no flow {flow_id!r}.")
