"""Step per la conversione dei tipi e il parsing delle date."""
from __future__ import annotations

from typing import Literal

import pandas as pd

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

ErrorMode = Literal["raise", "coerce"]
_VALID_ERRORS = ("raise", "coerce")


class CastTypes(PipelineStep):
    """Cambia il tipo di una o più colonne.

    Args:
        mapping: dizionario {colonna: dtype}. Il dtype può essere una stringa
            ("int", "float", "str", "bool") o un tipo numpy/pandas.
        errors: "raise" (default) solleva eccezione su valori non convertibili;
            "coerce" sostituisce i non convertibili con NaN (solo per tipi numerici).

    Raises:
        KeyError: se una colonna non esiste nel dataset.
        ValueError: se `errors` ha un valore non valido.
    """

    def __init__(
        self,
        mapping: dict[str, str],
        errors: ErrorMode = "raise",
    ) -> None:
        super().__init__()
        if errors not in _VALID_ERRORS:
            raise ValueError(
                f"errors must be one of {_VALID_ERRORS}; got {errors!r}"
            )
        self.mapping = dict(mapping)
        self.errors: ErrorMode = errors

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()

        missing = [c for c in self.mapping if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")

        for col, dtype in self.mapping.items():
            df[col] = self._cast_column(df[col], dtype)

        record = StepRecord(
            name=self.name,
            params={"mapping": self.mapping, "errors": self.errors},
        )
        return dataset.with_data(df, step_record=record)

    def _cast_column(self, series: pd.Series, dtype: str) -> pd.Series:
        """Cast di una singola colonna, rispettando la modalità errori."""
        if self.errors == "coerce" and dtype in ("int", "float", "Int64", "Float64"):
            # to_numeric supporta errors="coerce" (NaN sui non convertibili)
            casted = pd.to_numeric(series, errors="coerce")
            # Per "int" classico non possiamo avere NaN: fallback a Float64 nullable
            if dtype == "int":
                # Se ci sono NaN, restiamo float; altrimenti castiamo a int
                if casted.isna().any():
                    return casted  # float con NaN
                return casted.astype("int64")
            if dtype == "float":
                return casted.astype("float64")
            return casted.astype(dtype)

        # Modalità "raise" o tipi non numerici
        return series.astype(dtype)


class ParseDates(PipelineStep):
    """Converte colonne in datetime.

    Args:
        columns: nome o lista di nomi di colonne.
        format: formato strftime opzionale (es. "%d/%m/%Y").
            Se None, pandas tenta di inferirlo.
        errors: "raise" (default) o "coerce" (valori non parsabili → NaT).

    Raises:
        KeyError: se una colonna non esiste.
        ValueError: se `errors` ha un valore non valido.
    """

    def __init__(
        self,
        columns: str | list[str],
        format: str | None = None,
        errors: ErrorMode = "raise",
    ) -> None:
        super().__init__()
        if errors not in _VALID_ERRORS:
            raise ValueError(
                f"errors must be one of {_VALID_ERRORS}; got {errors!r}"
            )
        if isinstance(columns, str):
            columns = [columns]
        self.columns: list[str] = list(columns)
        self.format = format
        self.errors: ErrorMode = errors

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()

        missing = [c for c in self.columns if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")

        for col in self.columns:
            df[col] = pd.to_datetime(
                df[col],
                format=self.format,
                errors=self.errors,
            )

        record = StepRecord(
            name=self.name,
            params={
                "columns": self.columns,
                "format": self.format,
                "errors": self.errors,
            },
        )
        return dataset.with_data(df, step_record=record)