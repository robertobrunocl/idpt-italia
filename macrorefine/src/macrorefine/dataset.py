"""Dataset: wrapper immutabile attorno a un pandas DataFrame con history."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from macrorefine.history import History, StepRecord

if TYPE_CHECKING:
    from macrorefine.profiling import ProfileReport


class Dataset:
    """Wrapper immutabile su un pandas DataFrame.

    Ogni trasformazione produce un nuovo Dataset (via `with_data`),
    accumulando una History di StepRecord.
    """

    def __init__(self, data: pd.DataFrame, history: History | None = None) -> None:
        if not isinstance(data, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(data).__name__}")
        # Copia difensiva: garantisce immutabilità rispetto al df esterno
        self._data: pd.DataFrame = data.copy()  #il copy è necessario per evitare che modifiche al DataFrame originale influenzino il Dataset, garantendo così l'immutabilità del Dataset stesso.
        self._history: History = history if history is not None else History()

    # ----- Costruttori da file -----

    @classmethod
    def from_csv(cls, path: str | Path, **kwargs: Any) -> "Dataset":
        """Carica un Dataset da un file CSV."""
        return cls(pd.read_csv(path, **kwargs))

    @classmethod
    def from_parquet(cls, path: str | Path, **kwargs: Any) -> "Dataset":
        """Carica un Dataset da un file Parquet."""
        return cls(pd.read_parquet(path, **kwargs))

    # ----- Output su file -----

    def to_csv(self, path: str | Path, **kwargs: Any) -> None:
        """Scrive il Dataset in un file CSV (default: index=False)."""
        kwargs.setdefault("index", False)
        self._data.to_csv(path, **kwargs)

    def to_parquet(self, path: str | Path, **kwargs: Any) -> None:
        """Scrive il Dataset in un file Parquet."""
        self._data.to_parquet(path, **kwargs)

    # ----- Accesso ai dati -----

    def to_pandas(self) -> pd.DataFrame:
        """Ritorna una COPIA del DataFrame interno (immutabilità garantita)."""
        return self._data.copy()

    @property
    def columns(self) -> list[str]:
        return list(self._data.columns)

    @property
    def shape(self) -> tuple[int, int]:
        return self._data.shape

    @property
    def history(self) -> History:
        return self._history

    def head(self, n: int = 5) -> pd.DataFrame:
        return self._data.head(n).copy()

    # ----- Trasformazione (immutabile) -----

    def with_data(
        self,
        new_data: pd.DataFrame,
        *,
        step_name: str | None = None,
        step_record: StepRecord | None = None,
    ) -> "Dataset":
        """Ritorna un nuovo Dataset con i nuovi dati e la history aggiornata.

        Esattamente uno tra `step_name` e `step_record` deve essere fornito.
        """
        if step_record is None and step_name is None:
            raise ValueError("Provide either `step_name` or `step_record`.")
        if step_record is not None and step_name is not None:
            raise ValueError("Provide only one of `step_name` or `step_record`.")

        record = step_record if step_record is not None else StepRecord(name=step_name)  # type: ignore[arg-type]
        return Dataset(new_data, history=self._history.append(record))
    
    def with_columns_renamed(self, mapping: dict[str, str]) -> "Dataset":
        """Ritorna un nuovo Dataset con le colonne rinominate.

        Args:
            mapping: dizionario {nome_attuale: nuovo_nome}.

        Raises:
            KeyError: se una delle colonne nel mapping non esiste.
        """
        df = self.to_pandas()
        missing = [c for c in mapping if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in dataset: {missing}")
        df = df.rename(columns=mapping)
        return self.with_data(df, step_name="rename")

    # ----- Profiling -----

    def profile(self) -> "ProfileReport":
        """Esegue una diagnostica del dataset e ritorna un ProfileReport."""
        # Import lazy per evitare cicli
        from macrorefine.profiling import profile
        return profile(self)

    # ----- Repr -----

    def __repr__(self) -> str:
        rows, cols = self._data.shape
        return f"Dataset(rows={rows}, cols={cols}, history_steps={len(self._history)})"