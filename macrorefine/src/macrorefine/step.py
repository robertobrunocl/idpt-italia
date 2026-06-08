"""PipelineStep: classe base astratta per tutti gli step (built-in e custom)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


class PipelineStep(ABC):
    """Classe base per ogni step di una Pipeline.

    Sottoclassi devono implementare `apply(dataset) -> Dataset`.
    Il nome dello step viene preso dalla classe se non sovrascritto.
    """

    name: str = ""  # se vuoto, usato il nome della classe

    def __init__(self) -> None:
        # Imposta il nome di default come nome della classe
        if not type(self).__dict__.get("name"):
            self.name = type(self).__name__

    @abstractmethod
    def apply(self, dataset: "Dataset") -> "Dataset":
        """Applica la trasformazione e ritorna un NUOVO Dataset."""
        ...

    def __repr__(self) -> str:
        return f"{self.name}()"