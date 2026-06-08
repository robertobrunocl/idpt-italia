"""Recipe: pipeline pre-configurate per casi d'uso ricorrenti."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from macrorefine.pipeline import Pipeline

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


class Recipe(ABC):
    """Classe base per definire pipeline ricorrenti.

    Sottoclassare e implementare `build()` per dichiarare la Pipeline.
    Esempio:

        class MyRecipe(Recipe):
            def build(self) -> Pipeline:
                return Pipeline().add(NormalizeColumnNames()).add(DropEmptyColumns())

        clean = MyRecipe().apply(dataset)
    """

    @abstractmethod
    def build(self) -> Pipeline:
        """Costruisce la Pipeline associata alla recipe."""
        ...

    def apply(self, dataset: "Dataset") -> "Dataset":
        """Applica la Pipeline costruita al dataset."""
        return self.build().run(dataset)                                        