class SocelBuildError(Exception):
    """A log cannot be turned into an sOCEL as asked. The message says why."""


class UnknownClass(SocelBuildError):
    def __init__(self, kind: str, socel_class: str) -> None:
        super().__init__(f"{socel_class!r} is no {kind} class of the taxonomy.")


class UnknownType(SocelBuildError):
    def __init__(self, kind: str, name: str) -> None:
        super().__init__(f"The log has no {kind} {name!r}.")


class InvalidSocel(SocelBuildError):
    """The classified log breaks an sOCEL conformance rule."""


class InvalidRecordFile(SocelBuildError):
    """A record file cannot be read as one."""


class UnknownUpload(SocelBuildError):
    def __init__(self) -> None:
        super().__init__("The record file is no longer there; upload it again.")


class UndefinedFlow(SocelBuildError):
    def __init__(self, flow_id: str) -> None:
        super().__init__(f"The flow {flow_id!r} needs a unit and a category.")


class UnknownCategory(SocelBuildError):
    def __init__(self, category: str) -> None:
        super().__init__(f"{category!r} is no flow category of the taxonomy.")
