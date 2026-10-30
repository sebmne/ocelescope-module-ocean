class FlowNotFound(LookupError):
    """The flow addressed by a read operation does not exist in this view."""

    def __init__(self, flow_id: str) -> None:
        super().__init__(f"The log has no flow {flow_id!r}.")


class FactorCatalogUnavailable(RuntimeError):
    """The factor catalog is not configured, or cannot be consulted right now.
    The message says why."""


class UnknownFactorCatalog(LookupError):
    def __init__(self, catalog: str) -> None:
        super().__init__(f"There is no factor catalog {catalog!r}.")


class FactorCatalogNotConnected(FactorCatalogUnavailable):
    def __init__(self, name: str) -> None:
        super().__init__(f"{name} is not connected; connect it with a key first.")


class CatalogFactorNotFound(LookupError):
    def __init__(self, ref: str) -> None:
        super().__init__(f"The factor catalog has no factor {ref!r}.")


class IncompatibleUnit(ValueError):
    def __init__(self, ref: str, unit: str) -> None:
        super().__init__(f"The factor {ref!r} cannot be expressed per {unit!r}.")


class CatalogKeyRefused(ValueError):
    def __init__(self, catalog: str) -> None:
        super().__init__(f"{catalog} does not accept this key.")


class CatalogKeyFromEnvironment(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "The factor catalog's key is set in the environment (.env); change it there."
        )
