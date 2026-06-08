"""Step per combinare Dataset (join, enrichment)."""
from __future__ import annotations

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep


class LeftJoinEnrich(PipelineStep):
    """Arricchisce il Dataset con colonne di un altro Dataset tramite left join.

    Args:
        other: Dataset di lookup da cui prelevare le colonne aggiuntive.
        left_on: colonna o lista di colonne del Dataset corrente per il join.
        right_on: colonna o lista di colonne del Dataset di lookup per il join.
        columns: lista delle colonne di `other` da aggiungere al risultato.

    Note:
        Le righe che non trovano corrispondenza avranno NaN nelle colonne
        aggiunte. Le metriche dello step riportano `matched` e `unmatched`.
    """

    def __init__(
        self,
        other: Dataset,
        left_on: str | list[str],
        right_on: str | list[str],
        columns: list[str],
    ) -> None:
        super().__init__()
        self.other = other
        self.left_on = [left_on] if isinstance(left_on, str) else list(left_on)
        self.right_on = [right_on] if isinstance(right_on, str) else list(right_on)
        self.columns = list(columns)

        if len(self.left_on) != len(self.right_on):
            raise ValueError(
                f"left_on and right_on must have the same length; "
                f"got {len(self.left_on)} vs {len(self.right_on)}"
            )

    def apply(self, dataset: Dataset) -> Dataset:
        left_df = dataset.to_pandas()
        right_df = self.other.to_pandas()

        # Validazione
        missing_left = [c for c in self.left_on if c not in left_df.columns]
        if missing_left:
            raise KeyError(f"Columns not found in left dataset: {missing_left}")
        needed_right = list(set(self.right_on) | set(self.columns))
        missing_right = [c for c in needed_right if c not in right_df.columns]
        if missing_right:
            raise KeyError(f"Columns not found in right dataset: {missing_right}")

        # Subset del right per evitare di portare colonne non richieste
        right_subset = right_df[needed_right].copy()

        # Left join
        merged = left_df.merge(
            right_subset,
            how="left",
            left_on=self.left_on,
            right_on=self.right_on,
            suffixes=("", "_right"),
        )

        # Pulizia: rimuovi le right_on che hanno nome diverso da left_on
        for lc, rc in zip(self.left_on, self.right_on):
            if lc != rc and rc in merged.columns:
                merged = merged.drop(columns=[rc])

        # Metriche
        if self.columns:
            matched = int(merged[self.columns[0]].notna().sum())
        else:
            matched = len(merged)
        unmatched = len(merged) - matched

        record = StepRecord(
            name=self.name,
            params={
                "left_on": self.left_on,
                "right_on": self.right_on,
                "columns": self.columns,
            },
            metrics={"matched": matched, "unmatched": unmatched},
        )
        return dataset.with_data(merged, step_record=record)