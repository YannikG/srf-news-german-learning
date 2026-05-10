"""Errors from lexicon retrieval orchestration."""


class RetrievalServiceError(Exception):
    """Raised when embedding, sidecar start, or persistence steps fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
