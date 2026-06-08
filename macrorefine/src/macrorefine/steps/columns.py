"""Step che operano sulle colonne."""
from __future__ import annotations

import re

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep


def _to_snake_case(name: str) -> str:
    """Converte un nome di colonna in snake_case.

    Esempi:
        "FullName"     -> "full_name"
        "ID"           -> "id"
        "Full Name"    -> "full_name"
        "City "        -> "city"
        "name@home"    -> "name_home"
        "price($)"     -> "price"
    """
    # Inserisce underscore tra minuscola/numero e maiuscola: "FullName" -> "Full_Name"
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    # Tutto minuscolo
    s = s.lower()
    # Sostituisce caratteri non alfanumerici con underscore
    s = re.sub(r"[^a-z0-9]+", "_", s)
    # Rimuove underscore iniziali/finali e collassa quelli multipli
    s = re.sub(r"_+", "_", s).strip("_")
    return s


class NormalizeColumnNames(PipelineStep):
    """Normalizza i nomi delle colonne in snake_case."""

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        old_names = list(df.columns)
        new_names = [_to_snake_case(c) for c in old_names]
        df.columns = new_names

        renamed = {o: n for o, n in zip(old_names, new_names) if o != n}
        record = StepRecord(
            name=self.name,
            metrics={"renamed_count": len(renamed), "renamed": renamed},
        )
        return dataset.with_data(df, step_record=record)


class DropEmptyColumns(PipelineStep):
    """Rimuove colonne completamente vuote (tutti NaN/None)."""

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        df = df.drop(columns=empty_cols)
        record = StepRecord(
            name=self.name,
            metrics={"dropped_count": len(empty_cols), "dropped": empty_cols},
        )
        return dataset.with_data(df, step_record=record)


class DropColumns(PipelineStep):
    """Rimuove le colonne specificate."""

    def __init__(self, columns: list[str]) -> None:
        super().__init__()
        self.columns = list(columns)

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        missing = [c for c in self.columns if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")
        df = df.drop(columns=self.columns)
        record = StepRecord(
            name=self.name,
            params={"columns": self.columns},
            metrics={"dropped_count": len(self.columns)},
        )
        return dataset.with_data(df, step_record=record)
    

class RenameColumns(PipelineStep):
    """Rinomina colonne secondo un mapping {nome_vecchio: nome_nuovo}.

    Args:
        mapping: dizionario {colonna_attuale: nuovo_nome}.

    Raises:
        KeyError: se una colonna del mapping non esiste nel dataset.
        ValueError: se rinominare causerebbe un conflitto con una colonna esistente.
    """

    def __init__(self, mapping: dict[str, str]) -> None:
        super().__init__()
        self.mapping = dict(mapping)

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()

        missing = [c for c in self.mapping if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")

        # Verifica che i nuovi nomi non collidano con colonne esistenti
        # (escluse quelle che stiamo rinominando)
        survivors = set(df.columns) - set(self.mapping.keys())
        conflicts = [new for new in self.mapping.values() if new in survivors]
        if conflicts:
            raise ValueError(
                f"Renaming would create duplicate column names: {conflicts}"
            )

        df = df.rename(columns=self.mapping)
        record = StepRecord(
            name=self.name,
            params={"mapping": self.mapping},
            metrics={"renamed_count": len(self.mapping)},
        )
        return dataset.with_data(df, step_record=record)