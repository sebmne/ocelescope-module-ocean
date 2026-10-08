from typing import Protocol


class UploadStore(Protocol):
    """Keeps files the user uploaded until they are used."""

    def put(self, content: bytes) -> str:
        """Keep the content; returns the id to ask for it again."""
        ...

    def get(self, upload_id: str) -> bytes | None:
        """The content kept under the id, None when there is none."""
        ...
