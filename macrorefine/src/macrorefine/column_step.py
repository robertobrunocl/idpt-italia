"""ColumnStep: classe base per step che operano su colonne specifiche.

Riduce il boilerplate: la sottoclasse implementa solo `transform_column`,
mentre la classe base gestisce validazione, iterazione, history e immutabilità.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


class ColumnStep(PipelineStep):
    """Classe base per step che trasformano una o più colonne specifiche.

    Sottoclassare e implementare `transform_column(series, column_name)`.
    Tutto il resto (validazione delle colonne, iterazione, history record,
    immutabilità del Dataset) è gestito automaticamente.

    Esempio:

        class Uppercase(ColumnStep):
            def transform_column(self, series, column_name):
                return series.str.upper()

        pipeline.add(Uppercase(columns=["name", "city"]))

    Args:
        columns: Nome della colonna o lista di nomi di colonne su cui operare.
    """

    def __init__(self, columns: str | list[str]) -> None:
        super().__init__()
        if isinstance(columns, str):
            columns = [columns]
        self.columns: list[str] = list(columns)

    @abstractmethod
    def transform_column(
        self, series: pd.Series, column_name: str
    ) -> pd.Series:
        """Trasforma una singola colonna.

        Args:
            series: La Series originale.
            column_name: Il nome della colonna (utile per logica condizionale
                quando lo stesso step opera su più colonne).

        Returns:
            La Series trasformata, che sostituirà l'originale.
        """
        ...

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        missing = [c for c in self.columns if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")

        for col in self.columns:
            df[col] = self.transform_column(df[col], col)

        record = StepRecord(
            name=self.name,
            params={"columns": self.columns},
        )
        return dataset.with_data(df, step_record=record)