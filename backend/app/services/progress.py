from typing import Protocol


class ProgressReporter(Protocol):
    """Observador do andamento de uma tarefa longa (implementado pelo worker)."""

    def report(self, progress: float, message: str | None = None) -> None: ...

    def log(self, message: str) -> None: ...


class NullProgressReporter:
    def report(self, progress: float, message: str | None = None) -> None:
        pass

    def log(self, message: str) -> None:
        pass
