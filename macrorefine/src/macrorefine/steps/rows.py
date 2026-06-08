"""Step che operano sulle righe."""
from __future__ import annotations

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

from typing import Callable

import pandas as pd 


class DropDuplicateRows(PipelineStep):
    """Rimuove le righe duplicate."""

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        after = len(df)
        record = StepRecord(
            name=self.name,
            metrics={"removed_count": before - after},
        )
        return dataset.with_data(df, step_record=record)
    

class FilterRows(PipelineStep):
    """Filtra le righe in base a un predicato.

    Args:
        predicate: funzione che riceve il DataFrame e ritorna una Series
            booleana. Le righe con True vengono mantenute.

    Esempio:
        FilterRows(predicate=lambda df: df["data_fine"].isna() | (df["data_fine"] == "9999-12-31"))
    """

    def __init__(self, predicate: Callable[[pd.DataFrame], pd.Series]) -> None:
        super().__init__()
        self.predicate = predicate

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        before = len(df)
        mask = self.predicate(df)
        df = df[mask].reset_index(drop=True)
        after = len(df)
        record = StepRecord(
            name=self.name,
            metrics={
                "rows_before": before,
                "rows_after": after,
                "rows_removed": before - after,
            },
        )
        return dataset.with_data(df, step_record=record)