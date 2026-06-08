"""Step per la gestione dei valori mancanti."""
from __future__ import annotations

from typing import Any, Literal

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

Strategy = Literal["mean", "median", "constant"]
_VALID_STRATEGIES = ("mean", "median", "constant")


class FillMissing(PipelineStep):
    """Riempie i valori mancanti nelle colonne specificate.

    Args:
        columns: Colonne su cui operare.
        strategy: "mean", "median" o "constant".
        value: Valore da usare se strategy="constant".
    """

    def __init__(
        self,
        columns: list[str],
        strategy: Strategy = "mean",
        value: Any = None,
    ) -> None:
        super().__init__()
        if strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"strategy must be one of {_VALID_STRATEGIES}; got {strategy!r}"
            )
        if strategy == "constant" and value is None:
            raise ValueError("strategy='constant' requires a `value`.")
        self.columns = list(columns)
        self.strategy: Strategy = strategy
        self.value = value

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        missing = [c for c in self.columns if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found: {missing}")

        filled_count: dict[str, int] = {}
        for col in self.columns:
            n_missing = int(df[col].isna().sum())
            if self.strategy == "mean":
                fill_value = df[col].mean()
            elif self.strategy == "median":
                fill_value = df[col].median()
            else:  # constant
                fill_value = self.value
            df[col] = df[col].fillna(fill_value)
            filled_count[col] = n_missing

        record = StepRecord(
            name=self.name,
            params={"columns": self.columns, "strategy": self.strategy, "value": self.value},
            metrics={"filled_per_column": filled_count},
        )
        return dataset.with_data(df, step_record=record)